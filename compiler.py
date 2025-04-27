#!/usr/bin/env python3

import os
import sys
import argparse

from lexer import Lexer, Token, TokenType
from fileloader import FileLoader
from parser import Parser, Node, NodeType
from codegen import CodeGenerator

# Update compile_wake_to_masm to use the AST-based approach with include handling
def compile_wake_to_masm(input_file, output_file, verbose=False): # Add verbose parameter
    try:
        print(f"Compiling {input_file} to {output_file}")
        
        # Set up file loader with search paths
        base_dir = os.path.dirname(os.path.abspath(input_file))
        file_loader = FileLoader(base_dir)
        
        # Add standard search paths
        exec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        file_loader.add_search_path(exec_dir)
        file_loader.add_search_path(os.path.join(exec_dir, 'include'))
        file_loader.add_search_path(os.getcwd())
        
        # Process all includes and collect tokens
        tokens = file_loader.process_includes(input_file)
        
        # Debug output to check tokens (conditional)
        if verbose:
            print(f"Total tokens processed: {len(tokens)}")
            function_tokens = [t for t in tokens if t.type == TokenType.FUNCTION]
            print(f"Function declarations found: {len(function_tokens)}")
            
            # Show all function tokens and their source files
            for ft in function_tokens:
                idx = tokens.index(ft)
                if idx + 1 < len(tokens) and tokens[idx+1].type == TokenType.IDENTIFIER:
                    func_name = tokens[idx+1].value
                    source_file = ft.source_file
                    print(f"Found function: {func_name} from {source_file}")
        
        # Parse tokens into AST
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Debug AST (conditional)
        if verbose:
            function_nodes = [node for node in ast.children if node.type == NodeType.FUNCTION]
            print(f"Function nodes in AST: {len(function_nodes)}")
            for fn in function_nodes:
                print(f"Function in AST: {fn.value}")
        
        # Generate MASM code
        generator = CodeGenerator()
        masm_code = generator.generate(ast)
        
        # Write output
        with open(output_file, 'w') as outfile:
            outfile.write(masm_code)
        
        print(f"Wake file '{input_file}' successfully compiled to Masm file '{output_file}'")
        return True
        
    except SyntaxError as e:
        print(f"Syntax error: {str(e)}")
        return False
    except FileNotFoundError as e:
        print(f"File error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error compiling Wake to Masm: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # Default paths using os.path for proper path handling
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Remove default_input as it's no longer used for defaulting
    # default_input = os.path.join(base_dir, "main.wake")
    default_output_base = "main" # Base name for default output if input has no extension

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Compile Wake language files to Masm.")
    # Make input_file a required positional argument
    parser.add_argument('input_file',
                        help="The input .wake file")
    parser.add_argument('-o', '--output', dest='output_file', default=None,
                        help="The output .masm file (defaults to input filename with .masm extension)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose output for debugging")

    args = parser.parse_args()

    input_file = os.path.normpath(args.input_file)
    output_file = args.output_file
    verbose = args.verbose # Get verbose flag

    # Make sure input file exists (keep this check for a clear error)
    if not os.path.exists(input_file):
        # Use parser's error handling
        parser.error(f"Input file '{input_file}' not found")

    # If output file not specified, default based on input filename
    if output_file is None:
        input_basename = os.path.basename(input_file)
        # Determine output directory (same as input file)
        output_dir_default = os.path.dirname(input_file)
        if input_basename.lower().endswith('.wake'):
            output_basename = input_basename[:-5] + '.masm'
        else:
            # If input doesn't end with .wake, use its name + .masm
            output_basename = input_basename + '.masm'
        # Place output in the same directory as input by default
        output_file = os.path.join(output_dir_default, output_basename)
    else:
        output_file = os.path.normpath(output_file)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            if verbose: # Conditional print
                print(f"Created output directory: {output_dir}")
        except OSError as e:
            parser.error(f"Error creating output directory '{output_dir}': {str(e)}")

    # Compile the file, passing the verbose flag
    success = compile_wake_to_masm(input_file, output_file, verbose)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
