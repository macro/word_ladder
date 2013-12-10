-module(word_ladder).

-author(nchintomby@gmail.com).

-export([
    start/1,
    start/3,
    combinations/2,
    print_dict/1
]).

-define(READAHEAD_SIZE, 1024*4).
-define(FN, "/usr/share/dict/words").
%-define(FN, "words").

start(Args)->
    [Start, End | _] = lists:map(fun erlang:atom_to_list/1, Args),
    Size = erlang:length(Start),
    start(Size, Start, End).

start(Size, Start, End)->
    io:format("Paritioning words of length ~p ...~n", [Size]),
    GroupByPartition = with_line(?FN, get_grouper(Size), dict:new()),
    %print_dict(GroupByPartition),
    Graph = create_graph(GroupByPartition),
    %print_dict(Graph),
    GraphItems = dict:to_list(Graph),
    VCount = erlang:length(GraphItems),
    ECount = trunc(lists:foldr(fun({_K,V}, Acc0) ->
                                   Acc0 + erlang:length(V) 
                               end, 0, GraphItems) / 2),
    io:format("Finding word transformations in word graph (vertices=~p, edges=~p) ...~n", [VCount, ECount]),
    case bfs(Graph, Start, End) of
        [] -> io:format("No path found from ~p to ~p~n", [Start, End]);
        Path -> io:format("Found path from ~p to ~p:~n", [Start, End]),
        lists:foldr(
            fun(Word, Acc) ->
                io:format("  ~p: ~p~n", [Acc, Word]),
                Acc + 1
            end, 1, lists:reverse(Path))
    end.

create_graph(GroupByPartition) ->
    io:format("Building word graph ...~n", []),
    dict:fold(fun(_Partition, WordList, Acc) ->
                  lists:foldr(fun([V1,V2], Acc1) ->
                                  Acc2 = dict:append_list(V1, [V2], Acc1),
                                  dict:append_list(V2, [V1], Acc2)
                              end, Acc, combinations(gb_sets:to_list(WordList), 2))
              end, dict:new(), GroupByPartition).

bfs(Graph, Start, End) ->
    WithEdges = fun(_Self, Seen, Q, _Path, []) ->
                        [Seen, Q];  % exit condition
                   (Self, Seen, Q, Path, Edges) ->
                        %io:format("~p ~p ~p ~p ~n", [Seen, Path, Q, Edges]),
                        [V2|Edges1] = Edges,
                        case gb_sets:is_member(V2, Seen) of
                            true -> 
                                Self(Self, Seen, Q, Path, Edges1);
                            _ ->
                                Self(Self, gb_sets:add_element(V2, Seen), Q ++ [Path ++ [V2]], Path, Edges1)
                        end
                end,
    WithQueue = fun(_Self, _Seen, []) ->
                       [];  % no path found
                   (Self, Seen, [Path|Q]) ->
                       %io:format("~p ~p ~p ~n", [Seen, Path, Q]),
                       V1 = lists:last(Path),
                       case V1 of
                           End -> Path;  %  found end, return the path
                           _ ->
                               Edges = case dict:find(V1, Graph) of
                                   error -> [];  % no edges from vertex
                                   {ok, _Edges} -> _Edges
                               end,
                               [Seen1, Q1] = WithEdges(WithEdges, Seen, Q, Path, Edges),
                               Self(Self, Seen1, Q1)
                       end
                end,
    WithQueue(WithQueue, gb_sets:new(), [[Start]]).

%% @doc Cylces through all partition, calling the fun `F` for each partition.
with_partitions(_Hd, [], _F, Acc) ->
    Acc;
with_partitions(Hd, Tail, F, Acc) ->
    C = hd(Tail), 
    Tail1 = tl(Tail), 
    Acc1 = F(Hd ++ "?" ++ Tail1, Acc),
    with_partitions(Hd ++ [C], Tail1, F, Acc1). 

%% @doc Add word to its partition groups
get_grouper(Size) ->
    fun(Line, Dict) ->
        %io:format("~p", [Line]),
        [Word, _] = binary:split(Line, <<"\n">>),
        case erlang:byte_size(Word) of
            Size ->
                LowerWord = string:to_lower(binary:bin_to_list(Word)),
                F = fun(Partition, Acc) ->
                        Set = case dict:find(Partition, Acc) of
                            error -> gb_sets:new();
                            {ok, _Set} -> _Set
                        end,
                        dict:store(Partition, gb_sets:add_element(LowerWord, Set), Acc)
                    end,
                with_partitions([], LowerWord, F, Dict);
            _ ->
                Dict
        end
    end.

%% @doc Call the fun `F` for each line in the file.
with_line(FileName, F, Acc) ->
    {ok, Device} = file:open(FileName, [raw, read, binary, {read_ahead, ?READAHEAD_SIZE}]),
    Reader = fun(Self, Acc1) ->
        case file:read_line(Device) of
            eof -> Acc1;
            {ok, Line} -> 
                Acc2 = F(Line, Acc1),
                Self(Self, Acc2)
        end
    end,
    Ret = Reader(Reader, Acc),
    file:close(Device),
    Ret.

%% @doc Build combinations of size `R` with items in `L`.
combinations(_L, 0) ->
    [[]];
combinations([], _R) ->
    [];
combinations([Head|Rest], R) ->
    [[Head|SubList] || SubList <- combinations(Rest, R-1)] ++ combinations(Rest, R).
%
% misc
%
print_dict(Dict) ->
    dict:map(fun(Key, Value) ->
                io:format("~p: ~p~n", [Key, Value]),
                Value
            end, Dict).

