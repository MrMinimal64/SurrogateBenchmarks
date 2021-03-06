#! /usr/bin/env python
from argparse import ArgumentParser

import os
import socket
import subprocess
import sys
import time

import numpy

import daemon_whisperer

RNG = 1
numpy.random.seed(RNG)


def kill_server(socket_name, buffer_size=1024, end_str="."*10):
    # Tell Server to stop
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(socket_name)
    request = "STOP" + end_str
    s.send(request)
    data = s.recv(buffer_size)
    s.shutdown(socket.SHUT_WR)
    s.close()
    print "Should be 'Closing': %s" % data


def main():
    prog = "python daemonize_benchmark.py"
    parser = ArgumentParser(description="", prog=prog)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stop", dest="stop", default=False, action="store_true",
                       help="Tell daemon to stop")

    group.add_argument("--surrogateData", dest="surrogate_data", default=None,
                       help="Start daemon with loaded data")
    # IPC infos
    parser.add_argument("--pcs", dest="pcs", required=True)
    parser.add_argument("--socket", dest="socket", default=None, required=True,
                        help="Where to create socket?")
    parser.add_argument("--dry", dest="dry", default=False, action="store_true",
                        help="Print daemon call")

    args, unknown = parser.parse_known_args()

    if args.stop:
        kill_server(socket_name=args.socket)
        return

    # We are here, so we have to build a call
    # Prepare call
    socket_dir = args.socket
    if not os.path.isabs(socket_dir):
        socket_dir = os.path.normpath(os.path.abspath(socket_dir))

    surrogate_data = args.surrogate_data
    if not os.path.isabs(surrogate_data):
        surrogate_data = os.path.normpath(os.path.abspath(surrogate_data))

    pcs_file = args.pcs
    if not os.path.isabs(pcs_file):
        pcs_file = os.path.normpath(os.path.abspath(pcs_file))

    cmd = ["daemon_benchmark.py", "--socket", socket_dir, "--data",
           surrogate_data, "--pcs", pcs_file]

    sys.stdout.write(" ".join(cmd) + "\n")

    if not args.dry:
        print "START"
        cmd.append("--daemon")
        p = subprocess.Popen(cmd)
        sys.stdout.write(" ".join(cmd) + "\n")

        works = False
        try_ct = 0
        while try_ct < 20:
            answer = daemon_whisperer.whisper(socket_name=args.socket,
                                              message="SayHello")
            print "Daemon answers: ", answer
            if answer == "Hello =)":
                print "Deamon is now at your commands!"
                return
            time.sleep(5)
            try_ct += 1
        print "Could not bring daemon to life..."
        sys.exit(1)

    return

if __name__ == "__main__":
    main()
    sys.exit(0)
