#!/usr/bin/env python

"""
Generate client and server CURVE certificate files then move them into the
appropriate store directory, private_keys or public_keys.

In practice this would be done by hand or some out-of-band process.

"""
from argparse import ArgumentParser

import os
import shutil
import zmq.auth


def generate_certificates(base_dir, cert_folders_prefix, cert_files_prefix):
    """ Generate client and server CURVE certificate files
    """
    keys_dir = os.path.join(base_dir, 'certificates')
    public_keys_dir = os.path.join(
        base_dir, "{}public_keys".format(cert_folders_prefix))
    secret_keys_dir = os.path.join(
        base_dir, "{}private_keys".format(cert_folders_prefix))

    # Create directories for certificates, remove old content if necessary
    for d in [keys_dir, public_keys_dir, secret_keys_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.mkdir(d)

    # create new keys in certificates dir
    server_public_file, server_secret_file = \
        zmq.auth.create_certificates(
            keys_dir, "{}server".format(cert_files_prefix))
    if not os.path.exists(server_public_file):
        raise RuntimeError("Server public file creation error")
    if not os.path.exists(server_secret_file):
        raise RuntimeError("Server secret file creation error")

    client_public_file, client_secret_file = \
        zmq.auth.create_certificates(
            keys_dir, "{}client".format(cert_files_prefix))
    if not os.path.exists(client_public_file):
        raise RuntimeError("Client public file creation error")
    if not os.path.exists(client_secret_file):
        raise RuntimeError("Client secret file creation error")

    # move public keys to appropriate directory
    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key"):
            shutil.move(os.path.join(keys_dir, key_file),
                        os.path.join(public_keys_dir, '.'))

    # move secret keys to appropriate directory
    for key_file in os.listdir(keys_dir):
        if key_file.endswith(".key_secret"):
            shutil.move(os.path.join(keys_dir, key_file),
                        os.path.join(secret_keys_dir, '.'))

    # remove temporary keys directory
    if os.path.exists(keys_dir):
        shutil.rmtree(keys_dir)

if __name__ == '__main__':
    if zmq.zmq_version_info() < (4, 0):
        raise RuntimeError("Security is not supported in libzmq version < 4.0. "
                           "libzmq version {0}".format(zmq.zmq_version()))

    argparser = ArgumentParser(
        description='''Executable for launching a NIO instance'''
    )
    argparser.add_argument('-t', '--target', default=os.getcwd(),
                           help="Target dir where certificates dirs are saved")
    argparser.add_argument('-f', '--folders_prefix', default="",
                           help="Prefix to apply to certificate folders")
    argparser.add_argument('-k', '--cert_files_prefix', default="",
                           help="Prefix to apply to certificates")
    args = argparser.parse_args()

    generate_certificates(args.target,
                          args.folders_prefix,
                          args.cert_files_prefix)
