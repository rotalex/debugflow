
## DebugFlow: a service that checks and runs the code as you write it ##

Simple python debugger that parses and executes an unit test language.
If while, then show just first iteration, allow selecting specific iterations
in loops.

Specifications:
	* should work on incomplete code/ASTs
	* start and code sections with special markings: '###'
	* support only sections of code less than 50 instructions
	* support self contained code, no lateral effects, no function call evaluation
	* we select the starting points for "data flow" with ## and a list of values in the language we are interpreting
	* we annotate only identifiers with data flow values
	* each annotation overrides inferred/derived annotations
 
Interface:
	* introduce comments with a key-value structure under the analyzed line
	* for each expression we show the value on a a line
	* the comments cannot be longer than 10 lines for each line of code
	* and the length of a line is maximum 80 chars

Example:

// start the data flow debug region
###
```
#[("♠","J"), ("♡", "Q"), ("♢", "K"), ("♣", "A")]
def Straight(deck:list) -> list:
	one_hot = np.zeros(len(RANKS.ALL) + 1)
	# RANKS.ALL: "2 3 4 5 6 7 8 9 10 J Q K A"
	# len(RANKS.ALL): 11
	# len(RANKS.ALL) + 1
	# one_hot: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

	for card in deck:
		# deck: [("♠","J"), ("♡", "Q"), ("♢", "K"), ("♣", "A")]
		# card: ("♠","J")
		for i in RANKS.asIndex(card.rank):
			# card: ("♠","J")
			# card.rank: "J"
			# RANKS: class
			# RANKS.asIndex(card.rank): [0, 1] // evaluate function calls
			# i: 0
	for i in range(len(RANKS.ALL) - 1, -1, -1):
		# RANKS.ALL: "2 3 4 5 6 7 8 9 10 J Q K A"
		# len(RANKS.ALL): 11
		# range(len(RANKS.ALL) - 1, -1, -1): range
		# i: 10
		one_hot[i] += one_hot[i + 1] if one_hot[i] > 0 else 0
		# i: 10
		# one_hot[i]: 0
		# one_hot[i] > 0: False
		# one_hot[i + 1] if one_hot[i] > 0 else 0: 0
		# i: 10
		# one_hot[i]: 0
		# one_hot: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		if one_hot[i] >= 5:
			# i: 10
			# one_hot[i]: 0
			# one_hot[i] >= 5: False
			break
	else:
		return []
	hand = []
	# hand: []
	for j in range(i, i + 5):
		# i : 5 // revise
		# i + 5: 10 // revise
		# range(i, i + 5): range
		# j: 5 // revise
		hand.extend(deck.Card(ofRank = RANKS.fromIdx(j)))
		# j: 5 // revise
		# RANKS: class
		# RANKS.fromIdx(j): "5"
		# ofRank = "5"
		# deck.Card(ofRank = RANKS.fromIdx(j)): [("", "5")] // revise
		# hand: [("", "5")]
	return Deck(hand[::-1])
### // end the data flow debug region
```
