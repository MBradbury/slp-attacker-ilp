
int n =  ...;

range Nodes = 1..n;

{int} NodeSet = asSet(Nodes);

tuple Edge
{
	int u;
	int v;
}

{Edge} Edges with u in Nodes, v in Nodes = ...;
{int} Nbs[i in Nodes] = { j | <i,j> in Edges };

range S = 1..ftoi(round(2^n));

{int} Sub[s in S] = {i | i in Nodes:
	(s div ftoi(round(2^(i-1)))) mod 2 == 1 };
{int} Compl[s in S] = NodeSet diff Sub[s];

float Cost[Edges] = ...;

dvar boolean x[Edges];

constraint ctCut[S];

minimize
	sum(e in Edges) Cost[e] * x[e];

subject to {
	forall(s in S : 0 < card(Sub[s]) < n)
		ctCut[s]:
			sum(i in Sub[s], j in Nbs[i] inter Compl[s]) x[<i,j>] +
			sum(i in Compl[s], j in Nbs[i] inter Sub[s]) x[<i,j>] >= 1;
		
		ctAll:
			sum(e in Edges) x[e] == n-1;
}

{Edge} Used = {e | e in Edges : x[e] == 1};

execute
{
	writeln("Used edges=", Used)
}
