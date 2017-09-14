using CP;

tuple Coords
{
	float x;
	float y;
}

tuple Edge
{
	int u;
	int v;
}

tuple Message
{
	int src;
	int msg;
}

int obj = ...;

// Network
int num_nodes = ...; // Number of nodes in the network
float comms_range = ...; // The range of the nodes
{int} SourceIDs = ...; // The ids of the source nodes
{int} SinkIDs = ...;

range Nodes = 1..num_nodes;

assert forall (sink_id in SinkIDs) sink_id in Nodes;
assert forall (source_id in SourceIDs) source_id in Nodes;

Coords Coordinates[i in Nodes] = ...;

// Attacker
int attacker_start_pos = ...; // The id of the node the attacker starts at
float attacker_range = ...; // The distance the attacker can hear messages from

assert attacker_start_pos in Nodes;

// Routing

float source_period = ...; // seconds between messages
float safety_period = ...;

int slots_per_second = ...;

// Time 0 is special, it is for setting the attacker's initial move
int max_time = ftoi(ceil(safety_period * slots_per_second));
range Times = 0..max_time; // One tenth of a second
int source_period_quantised = ftoi(ceil(source_period * slots_per_second));

int num_normal_messages_per_source = ftoi(ceil(safety_period * source_period));
int num_normal_messages = num_normal_messages_per_source * card(SourceIDs);
int num_fake_messages = ...;
int num_total_messages = num_normal_messages + num_fake_messages;

sorted {Message} SourceMessages = { <s,m> | s in SourceIDs, m in 1..num_normal_messages_per_source };
sorted {Message} FakeMessages = { <num_nodes+1,m> | m in 1..num_fake_messages };
sorted {Message} AllMessages = SourceMessages union FakeMessages;

// Network constructs

float Distance[i in Nodes][j in Nodes] = 
	sqrt((Coordinates[i].x - Coordinates[j].x)^2 +
	     (Coordinates[i].y - Coordinates[j].y)^2);

// Eliminate self-self moves as when a node bcasts it will not receive a message sent by itself
{Edge} Edges with u in Nodes, v in Nodes = { <u,v> | u,v in Nodes : Distance[u][v] <= comms_range && u != v };
{int} NeighboursFrom[i in Nodes] = { j | <i,j> in Edges : i != j };
{int} NeighboursTo[i in Nodes] = { j | <j, i> in Edges : i != j };

// Attacker edges excluding ones leaving the source.
// The attacker will stay at the source node once it reaches it.
{Edge} AttackerEdges with u in Nodes, v in Nodes =
                              { <u,v> | u,v in Nodes : Distance[u][v] <= attacker_range } diff
                              { <s,v> | s in SourceIDs, v in Nodes : s != v };
{int} AttackerNeighboursFrom[i in Nodes] = { j | <i,j> in AttackerEdges : i != j };
{int} AttackerNeighboursTo[i in Nodes] = { j | <j, i> in AttackerEdges : i != j };

// Others

// Which nodes broadcast which messages at which time.
dvar boolean broadcasts[Nodes][AllMessages][Times];

// What path does the attacker take
dvar boolean attacker_path[Times][AttackerEdges];

// Did the attacker move to n at t
dexpr int attacker_moved_to_at[n in Nodes][t in Times] =
	(sum (e in AttackerEdges : e.v == n) attacker_path[t][e]) == 1;

// Did the attacker to a neighbour of n at t
// (Can the attacker get to n from the location it ended at?)
dexpr int attacker_moved_to_neighbour_at[n in Nodes][t in Times] =
	(sum (e in AttackerEdges : e.v in AttackerNeighboursTo[n]) attacker_path[t][e]) == 1;

// Did the attacker do a self-self move at t
dexpr int attacker_self_move[t in Times] =
	(sum (e in AttackerEdges : e.u == e.v) attacker_path[t][e]) == 1;

// Did the attacker move because of the message m at t
dexpr int attacker_moved_because_at[m in AllMessages][t in Times] =
	(sum (e in AttackerEdges : e.u != e.v)
		(attacker_path[t][e] == 1 && broadcasts[e.v][m][t] == 1)) == 1;

dexpr int node_generated_fake_message_at[n in Nodes][m in FakeMessages][t in Times] =
	broadcasts[n][m][t] == 1 &&
	(sum (neigh in NeighboursTo[n]) sum (t2 in Times : 0 < t2 < t) broadcasts[neigh][m][t2]) == 0;

dexpr int message_latency[m in SourceMessages] =
	// Need to find receive time
	min(sink_id in SinkIDs, n in NeighboursTo[sink_id], t in Times)
		((broadcasts[n][m][t] == 1) ? t : 10000)
	-
	// Need to find send time
	min(source_id in SourceIDs, t in Times)
		((broadcasts[source_id][m][t] == 1) ? t : 10000);




// Objective dexprs

// Maximise the distance between the attacker and the source (works)
dexpr float attacker_source_distance_obj =
	-(sum(s in SourceIDs) sum(e in AttackerEdges) (attacker_path[max_time][e] * Distance[s][e.v]));

// Just find a solution where the attacker does not find the source (works)
dexpr int attacker_find_source_obj =
	(sum(e in AttackerEdges : e.v in SourceIDs) attacker_path[max_time][e]);

// Optimise for energy usage (not working)
dexpr int energy_usage_obj =
	// If the attacker finds the source, then weight this run poorly
	(sum(e in AttackerEdges : e.v in SourceIDs) (attacker_path[max_time][e] * 1000)) +
	
  	// Minimise the number of messages sent
	(sum(n in Nodes) sum(m in AllMessages) sum(t in Times) broadcasts[n][m][t]);

// Minimise the number of moves the attacker makes from one node to a different node (works)
dexpr int attacker_moves_obj =
	sum(e in AttackerEdges : e.u != e.v) sum(t in Times)
	  (attacker_path[t][e] == 1);

// Minimise the latency between when a message is sent and when it is received (working)
dexpr float message_latency_obj =
	// If the attacker finds the source, then weight this run poorly
	(sum(e in AttackerEdges : e.v in SourceIDs) (attacker_path[max_time][e] * 1000)) +

  	sum(m in SourceMessages) message_latency[m];

assert obj >= 0 && obj <= 4;

dexpr float objective_value =
	obj == 0 ? attacker_source_distance_obj :
	obj == 1 ? attacker_find_source_obj :
	obj == 2 ? energy_usage_obj :
	obj == 3 ? attacker_moves_obj :
	obj == 4 ? message_latency_obj :
	infinity;

minimize objective_value;

// TODO: Look into using staticLex to prioritise multiple objectives
//minimize staticLex(attacker_find_source_obj, message_latency_obj);

subject to {

	ctR01: // No messages are sent at t=0
	forall (n in Nodes)
	  forall (m in AllMessages)
	    broadcasts[n][m][0] == 0;
	
	ctR02: // When do source nodes send messages
	forall (n in SourceIDs)
	  forall (m in SourceMessages : m.src == n)
	    broadcasts[n][m][((m.msg - 1) * source_period_quantised) + 1] == 1;
	
	ctR03: // No node sends more than one message concurrently
	forall (t in Times : t > 0) // Optimisation as t=0 no messages are sent
	  forall (n in Nodes)
	    (sum (m in AllMessages) broadcasts[n][m][t]) <= 1;
	
	ctR04: // Once a message is sent by one node it is never sent by that node again
	forall (m in AllMessages)
	  forall (n in Nodes)
	    forall (t1 in Times : t1 > 0)
	      (broadcasts[n][m][t1] == 1) => (sum (t2 in Times : t2 > t1) broadcasts[n][m][t2]) == 0;
	
	ctR05: // Source Messages can only be forwarded after a neighbour has sent it
	forall (n in Nodes : n not in SourceIDs) // Source nodes are exempt here, as they generate the message.
	  forall (m in SourceMessages)
	    forall (t1 in Times : t1 > 0)
	      (broadcasts[n][m][t1] == 1) => 
	      	(sum (neigh in NeighboursTo[n]) sum(t2 in Times : 0 < t2 < t1) broadcasts[neigh][m][t2]) >= 1;
	
	ctR06: // Messages sent by source must reach at least one sink
	forall (m in SourceMessages)
	  (sum (sink_id in SinkIDs) sum (n in NeighboursTo[sink_id]) sum (t in Times : t > 0) broadcasts[n][m][t]) >= 1;
	
	if (num_fake_messages > 0)
	{
		ctF01: // Once a fake messages has been generated at one node, it will never be generated at another node
		forall (n1 in Nodes)
		  forall (t1 in Times : t1 > 0)
		    forall (m in FakeMessages)
		    	(node_generated_fake_message_at[n1][m][t1] == 1) =>
		    		(sum (n2 in Nodes) sum (t2 in Times : t2 > t1)
		    			(node_generated_fake_message_at[n2][m][t2] == 1)) == 0;
		
		ctF02: // Fake Messages can only be forwarded after a neighbour has sent it
		forall (n in Nodes)
		  forall (m in FakeMessages)
		    forall (t1 in Times : t1 > 0)
		      (broadcasts[n][m][t1] == 1 && node_generated_fake_message_at[n][m][t1] == 0) => 
		        (sum (neigh in NeighboursTo[n]) sum(t2 in Times : 0 < t2 < t1) broadcasts[neigh][m][t2]) >= 1;
    }
	
	// The first attacker move at the special time t=0 is the self-self move.
	ctA01:
	attacker_path[0][<attacker_start_pos,attacker_start_pos>] == 1;
	
	ctA02: // Attacker makes exactly one move each time step (This may be the self-self move)
	forall (t in Times)
	  (sum (e in AttackerEdges) attacker_path[t][e]) == 1;
	
	ctA03: // Attacker must move from its current position (t > 0)
	forall (t in Times : t > 0)
	  (sum (e1, e2 in AttackerEdges : e1.v == e2.u)
	  	(attacker_path[t-1][e1] == 1 && attacker_path[t][e2] == 1)) == 1;
	
	// The attacker only moves when a message is broadcasted. It cannot move on its own.
	ctA04:
	forall (n in Nodes)
	  forall (t in Times : t > 0)
	    // If an attacker moves to n at t
	    ((sum (e in AttackerEdges : e.v == n && e.u != e.v) attacker_path[t][e]) == 1) =>
	      // Then it must be because n broadcasted m
	      (sum (m in AllMessages) broadcasts[n][m][t]) == 1;
	  	
	// The attacker only moves when a message is sent and that message has not been previously responded to
	ctA05: // Attacker can only move in response to sent messages
	forall (n in Nodes)
	  forall (m in AllMessages)
        forall (t in Times : t > 0)
          // if node n sent m at t
		  (broadcasts[n][m][t] == 1) &&
		  // and the attacker moved to a node at t-1 that can reach n at t
		  (attacker_moved_to_neighbour_at[n][t-1] == 1) &&
		  // and the attacker has never moved in response to m before
		  (sum (t2 in Times : 0 < t2 < t) (attacker_moved_because_at[m][t2] == 1)) == 0
		
		  // then the attacker moves in response to this message
		  => attacker_moved_to_at[n][t] == 1;
		  
	ctA06: // Attacker only moves once per message
	forall (t1 in Times : t1 > 0)
	  forall (m in AllMessages)
	    // If at t1 the attacker moved in response to the message m
	    attacker_moved_because_at[m][t1] == 1 =>
	      // Then at no subsequent time can the attacker move in response to m again
	      (sum (t2 in Times : t2 > t1) (attacker_moved_because_at[m][t2] == 1)) == 0;
	
	ctA07: // Attacker does not move when no neighbours send a message (t > 0)
	forall (t in Times : t > 0)
	  forall (e in AttackerEdges)
	    (attacker_path[t-1][e] == 1 && (sum (n in AttackerNeighboursTo[e.v]) sum (m in AllMessages) broadcasts[n][m][t]) == 0) =>
	      attacker_self_move[t] == 1;
};

{Edge} Used[t in Times] = {e | e in AttackerEdges : attacker_path[t][e] == 1};

{int} BroadcastsAt[n in Nodes][m in AllMessages] = {t | t in Times : broadcasts[n][m][t] == 1};

execute
{
	writeln("coords = \"\"\"", Coordinates, "\"\"\"")
	writeln("neighbours_to = \"\"\"", NeighboursTo, "\"\"\"")
	writeln("neighbours_from = \"\"\"", NeighboursFrom, "\"\"\"")
	writeln("range = ", comms_range)
	writeln("source_ids = ", SourceIDs)
	writeln("sink_ids = ", SinkIDs)
	writeln("attacker_start_pos = ", attacker_start_pos)
	writeln("attacker_range = ", attacker_range)
	writeln("attacker_neighbours_to = \"\"\"", AttackerNeighboursTo, "\"\"\"")
	writeln("attacker_neighbours_from = \"\"\"", AttackerNeighboursFrom, "\"\"\"")
	writeln("normal_messages = ", num_normal_messages)
	writeln("fake_messages = ", num_fake_messages)
	writeln("messages = ", num_total_messages)
	writeln("slots_per_second = ", slots_per_second)
	writeln("source_period = ", source_period)
	writeln("safety_period = ", safety_period)
	writeln("objective = ", obj)
	
	writeln("attacker_source_distance_obj = ", -attacker_source_distance_obj)
	writeln("attacker_find_source_obj = ", attacker_find_source_obj)
	writeln("energy_usage_obj = ", energy_usage_obj)
	writeln("attacker_moves_obj = ", attacker_moves_obj)
	writeln("message_latency_obj = ", message_latency_obj)
	
	writeln("used_edges = \"\"\"", Used, "\"\"\"")
	writeln("broadcasted_at = \"\"\"", BroadcastsAt, "\"\"\"")
	writeln("message_latency = \"\"\"", message_latency, "\"\"\"")
}
