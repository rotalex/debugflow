import pdb
import ast
import parser
from pprint import pprint

prompt = pdb.Pdb()

def indentLvl(codeLine):
	tabCnt = 0
	spcCnt = 0

	for ch in codeLine:
		tabCnt += (ch == '\t')
		spcCnt += (ch == ' ')

	if tabCnt:
		return tabCnt

	if spcCnt:
		return spcCnt // 4

def stripIndent(codeLine, indents=1):
	# consider tab = 4 space
	if codeLine[0] == '\t':
		return codeLine[indents:] # indents tabs
	if codeLine[0] == ' ':
		return codeLine[indents * 4:]
	return codeLine

def runTest(tree, lines, interpreter):
	pprint(list(enumerate(lines)))
	for node in ast.walk(tree):
		if not isinstance(node, ast.Module) and \
			not isinstance(node, ast.FunctionDef):
			continue
		if isinstance(node, ast.FunctionDef):
			comments = lines[node.lineno - 2][4:]
			values = eval(comments)
			for idx, funcArg in enumerate(node.args.args):
				print("funcArg = ", ast.dump(funcArg))

				#code = f"{funcArg.arg} = {values[idx]}"
				#print(f"Interpret[{code}] **")
				#interpreter.interpret(code)
				#print(f"->[{interpreter.getoutput()}]")
		for stmt in node.body:
			print(lines[stmt.lineno - 1])

			code = "%s" % lines[stmt.lineno]
			code = stripIndent(code)
			print(f"Interpret[{code}] **")
			interpreter.run(code)
			print(interpreter.frame_returning)
			#if isinstance(stmt, ast.Assign):
			#	stored = "%s" % stmt.targets[0].id
			#	interpreter.interpret(stored)
			#	print(f"#{stored} = {interpreter.getoutput()}")


def runTests(interpreter):
	with open("scenarios.py", "r") as f:
		allText = f.read().split("#$#$")
		for test in allText[1:2]:
			lines = test.split("\n")
			tree = ast.parse(test)
			runTest(tree, lines, interpreter)



if __name__ == "__main__":
	runTests(prompt)
