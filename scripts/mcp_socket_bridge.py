"""Relay stdio MCP bytes to a local Unix socket. No tools or credentials here."""

import socket
import sys
import threading


def relay(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(20)
        connection.connect(path)
        # Model turns may leave MCP idle; workflow/client deadlines bound waits.
        connection.settimeout(None)

        def upload():
            try:
                while data := sys.stdin.buffer.read1(65536):
                    connection.sendall(data)
            except OSError:
                pass  # The receiving loop reports connection failure without payloads.
            finally:
                try:
                    connection.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        threading.Thread(target=upload, daemon=True).start()
        while data := connection.recv(65536):
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2 or not sys.argv[1].startswith("/"):
            raise ValueError("Expected absolute socket path")
        relay(sys.argv[1])
    except (OSError, ValueError):
        print("MCP local service connection unavailable.", file=sys.stderr)
        raise SystemExit(1) from None
