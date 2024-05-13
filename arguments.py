import argparse


def argument_definition():

    parser = argparse.ArgumentParser()

    parser.add_argument("--host", default="127.0.0.1",
                        help="ip where server is host")

    parser.add_argument("-p", "--port", type=int, default=5000,
                        help="port where server is setup")

    parser.add_argument("-d", "--directory", default="file_server",
                        help="server's file storage directory")

    parser.add_argument("-f", "--folder", default="bares",
                        help="server's file storage folder")

    parser.add_argument("-i", "--header", default=0,
                        help="Index for the dataset header")

    parser.add_argument("-s", "--sep", default=',',
                        help="Separator of CSV")

    parser.add_argument("-e", "--encoding", default='latin1',
                        help="Encodign of CSV")

    arguments = parser.parse_args()

    return arguments
