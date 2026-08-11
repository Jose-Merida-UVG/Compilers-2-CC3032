
import sys
 
from compiler import analyze_file
 
 
def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python3 main.py <path-to-source-file>", file=sys.stderr)
        sys.exit(1)
 
    result = analyze_file(sys.argv[1])
 
    for err in result["errors"]:
        print(err)
 
    print(result["status_message"])
 
 
if __name__ == "__main__":
    main()
