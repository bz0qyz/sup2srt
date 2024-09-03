import subprocess
import time
import os
from exceptions import SubProcessError

class RunCommand:


    def run_command_return_output(self, command: list):
        """
        Runs a command in a subprocess and returns the output.

        :param command: The command to run, as a list (e.g., ['ping', '-c', '5', 'google.com'])
        :return: A tuple containing the return code, stdout, and stderr

        Example usage:
        return_code, output, error = run_command_and_return_result(['echo', 'Hello, World!'])
        print(f"Return code: {return_code}")
        print(f"Output: {output}")
        print(f"Error: {error}")
        """
        try:
            # Run the command and capture the output
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard error
                text=True,               # Treat output as text
                check=True               # Raise an exception if the command fails
            )

            # Return the command's return code, stdout, and stderr
            return result.returncode, result.stdout, result.stderr

        except subprocess.CalledProcessError as e:
            # Handle command failure (non-zero exit code)
            print(f"Command failed with exit code {e.returncode}")
            print(f"Error output: {e.stderr}")
            return e.returncode, e.stdout, e.stderr

    def run_command_with_scroll_window(self, command, height=None, header=None):
        """
        Runs a command in a subprocess and displays the output in a smaller 
        scrolling window within the terminal.

        :param command: The command to run, as a list (e.g., ['ping', '-c', '5', 'google.com'])
        :param height: The height of the scrolling window in lines
        :param header: a list of strings to show above the output window

        Example usage:
        run_command_with_scroll_window(['ping', '-c', '20', 'google.com'], height=10)  # Replace with your desired command

        """
        # Get the terminal size
        term_columns, term_lines = os.get_terminal_size()

        # remove header height from the terminal lines
        if header:
            term_lines = (term_lines - (len(header) + 4))
            header_banner = "-" * term_columns
            header = f"{header_banner}\n{'\n'.join(header)}\n{header_banner}"

        # calculate the window height if a percent
        if not height:
            height = term_lines
        if isinstance(height, str) and height.endswith('%'):
            height = int(height.replace('%', ''))
            height = (term_lines * (height / 100))

        # Start the subprocess
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            text=True,  # Handle output as text
            bufsize=1   # Line-buffered output
        )

        # ANSI escape sequences for cursor control
        clear_screen = '\033[2J'   # Clear the screen
        move_cursor_up = f'\033[{height}A'  # Move cursor up by window height
        move_cursor_to_top = '\033[H'  # Move cursor to the top of the screen

        # Initialize a list to store lines to display in the window
        output_buffer = []

        try:      
            # Clear the screen and print the prepend header once
            print(clear_screen, end='')  # Clear the screen
            # if header:
            #     print(f"first:{header}\n" + "-" * term_columns) 

            # Continuously read from the process output
            for line in process.stdout:
                # Append the new line to the buffer
                output_buffer.append(line)

                # Keep only the last 'height' lines in the buffer
                if len(output_buffer) > height:
                    output_buffer.pop(0)

                # Print the scrolling window effect
                print(move_cursor_to_top, end='')  # Move cursor to the top to maintain the header position
                if header:
                    print(f"{header}\n")  # Re-print the header and underline it
                # print(move_cursor_up, end='')  # Move cursor up to maintain window size

                        
                # Print the lines in the window
                for buffered_line in output_buffer:
                    print(buffered_line, end='')  # Print each line without adding extra newlines

                # Slight delay to simulate real-time output (adjust as needed)
                time.sleep(0.05)

        except KeyboardInterrupt:
            process.terminate()
            raise SubProcessError("Process interrupted.")

        # Wait for the process to finish and capture the exit code
        return_code = process.wait()
        if return_code != 0:
            raise SubProcessError(f"Command exited with code {return_code}")