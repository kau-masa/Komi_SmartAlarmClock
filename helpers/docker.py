#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import subprocess
import sys

from string import Template

DOCKER_IMAGE_NAME_RE = re.compile(r"^([a-zA-Z0-9_.]+/)?[a-zA-Z0-9_.]+$")
DOCKER_IMAGE_TAG_RE = re.compile(r"^[a-zA-Z0-9_.]+$")
ARCHIVE_NAME_VALID_CHAR_RE = re.compile(r"^[a-zA-Z0-9_]")

def docker_image_str(v):
    if DOCKER_IMAGE_NAME_RE.match(v):
        return v
    else:
        raise argparse.ArgumentTypeError("'{}' is not a valid Docker image name".format(v))

def docker_tag_str(v):
    if DOCKER_IMAGE_TAG_RE.match(v):
        return v
    else:
        raise argparse.ArgumentTypeError("'{}' is not a valid Docker tag name".format(v))

def run(args=[], wd=os.getcwd(), verbose=False):
    args_str = " ".join(args)
    if verbose:
        print "--- Running '{}'...".format(args_str)
        returncode = subprocess.call(args, cwd=wd)
        sys.stdout.flush()
        if returncode != 0:
            print "--- Error while running '{}'! See above for details".format(args_str)
            return False
        else:
            return True
    else:
        try:
            output = subprocess.check_output(
                args,
                stderr=subprocess.STDOUT,
                cwd=wd)
            return True
        except subprocess.CalledProcessError, e:
            print "--- Error while running '{}'! See below for details".format(args_str)
            print e.output
            print "---"
            return False

def templated_run(templated_args=[], cfg_dict={}, wd=os.getcwd(), verbose=False):
    args = []
    for templates_arg in templated_args:
        arg = Template(templates_arg).substitute(**cfg_dict)
        args.append(arg)

    return run(args=args, wd=wd, verbose=verbose)

def load_configuration(cfg_file="package.json"):
    # Loading the configuration file
    cfg_dict = dict()
    with open(cfg_file) as cfg_file_data:
        cfg_dict = json.load(cfg_file_data)

    # Setupping the 'file_dir' variable
    file_dir = os.path.dirname(os.path.abspath(cfg_file))
    docker_file_dir = file_dir
    if sys.platform == "win32":
        drive, path = os.path.splitdrive(file_dir)
        drive_letter = drive.replace(":","").lower()
        path_to = path.replace("\\","/")
        docker_file_dir =  "/" + drive_letter + path_to

    cfg_dict["file_dir"] = file_dir
    cfg_dict["docker_file_dir"] = docker_file_dir

    cfg_dict["file"] = cfg_file

    return cfg_dict

def create_args_parser(cfg_dict):
    # Parse command line arguments
    args_parser = argparse.ArgumentParser(
        description="Build '{}' Docker image".format(cfg_dict["name"]),
        epilog="Configuration (incl. default parameters value) are loaded from '{}'".format(cfg_dict["file"]))
    args_parser.add_argument(
        "--name",
        dest="image_name",
        type=docker_image_str,
        help="Docker image name (default is '%(default)s')")
    args_parser.add_argument(
        "--tag",
        dest="image_tag",
        type=docker_tag_str,
        help="Docker image tag (default is '%(default)s')")
    args_parser.add_argument(
        "--version",
        help="Version (default is '%(default)s')")
    args_parser.add_argument(
        "--build",
        help="Build identifier (default is '%(default)s')",
        default="internal")
    args_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Increase verbosity")

    args_parser.add_argument(
        "--skip_build",
        dest="do_build",
        action="store_false",
        help="Skip the image build (make sure the image has been built before)")
    if "image_test" in cfg_dict:
        args_parser.add_argument(
            "--test",
            dest="test",
            action="store_true",
            help="Test the image")
    args_parser.add_argument(
        "--save",
        dest="save",
        action="store_true",
        help="Save the image as a '.tar'")
    args_parser.add_argument(
        "--push",
        dest="push",
        action="store_true",
        help="Push the image to Docker Hub")

    return args_parser

def parse_args(args_parser, cfg_dict):
    args_parser.set_defaults(**cfg_dict)
    cfg_dict.update(vars(args_parser.parse_args()))

    cfg_dict["full_image_name"] = cfg_dict["image_name"] + ":" + cfg_dict["image_tag"]

    cfg_dict["image_out_file"] =  os.path.join(
        "out",
        "{}_{}_{}.tar".format(
                "".join(c if ARCHIVE_NAME_VALID_CHAR_RE.match(c) else "_" for c in cfg_dict["image_name"]),
                "".join(c if ARCHIVE_NAME_VALID_CHAR_RE.match(c) else "_" for c in cfg_dict["image_tag"]),
                "".join(c if ARCHIVE_NAME_VALID_CHAR_RE.match(c) else "" for c in cfg_dict["build"])))

    return cfg_dict

def build(cfg_file="package.json"):
    # Load the configuration
    cfg_dict = load_configuration(cfg_file)

    # Create the cli agument parser
    args_parser = create_args_parser(cfg_dict)

    ## Parse the cli arguments
    cfg_dict = parse_args(args_parser, cfg_dict)


    print ("Building docker image for '{}', version '{}' ({})...".format(
        cfg_dict["name"],
        cfg_dict["version"],
        cfg_dict["build"]))

    if cfg_dict["do_build"]:
        if not templated_run(
                templated_args=["docker", "build", "-t", "${full_image_name}", "."],
                cfg_dict=cfg_dict,
                wd=cfg_dict["file_dir"],
                verbose=cfg_dict["verbose"]):
            exit(1)

    print ("-- Docker image '{}' built successfully".format(cfg_dict["full_image_name"]))

    if "image_test" in cfg_dict and cfg_dict["test"]:
        success = True
        for docker_test_raw_args in cfg_dict["image_test"]:
            if not templated_run(
                    templated_args=docker_test_raw_args,
                    cfg_dict=cfg_dict,
                    wd=cfg_dict["file_dir"],
                    verbose=cfg_dict["verbose"]):
                success = False

        if not success:
            exit(2)

        print ("-- Docker image '{}' tested successfully".format(image_name))

    if cfg_dict["save"]:
        image_package_path = os.path.join(cfg_dict["file_dir"], cfg_dict["image_out_file"])
        if not os.path.exists(os.path.dirname(image_package_path)):
            os.makedirs(os.path.dirname(image_package_path))

        if not templated_run(
                templated_args=["docker", "save", "-o", "${docker_file_dir}/${image_out_file}", "${full_image_name}"],
                cfg_dict=cfg_dict,
                wd=cfg_dict["file_dir"],
                verbose=cfg_dict["verbose"]):
            exit(3)

        print ("-- Docker image successfully saved to '{}'".format(image_package_path))

    if cfg_dict["push"]:
        if not templated_run(
                templated_args=["docker", "push", "${full_image_name}"],
                cfg_dict=cfg_dict,
                wd=cfg_dict["file_dir"],
                verbose=cfg_dict["verbose"]):
            exit(4)

        print ("-- Docker image successfully pushed to Docker Hub")
