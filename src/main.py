import sys
from antlr4 import FileStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from error_listener import CompiscriptErrorListener

input_stream = FileStream(sys.argv[1], encoding="utf-8")
lexer = CompiscriptLexer(input_stream)

error_listener = CompiscriptErrorListener()
lexer.removeErrorListeners()
lexer.addErrorListener(error_listener)

tokens = CommonTokenStream(lexer)
parser = CompiscriptParser(tokens)
parser.removeErrorListeners()
parser.addErrorListener(error_listener)

tree = parser.program()

for err in error_listener.errors:
    print(err)

print(tree.toStringTree(recog=parser))
