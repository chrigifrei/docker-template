#!/usr/bin/env python
DESC=''' Dockerbuild Helper Script
'''
EPILOG='''
Build Environment:
    - build dir: dockerbuild
    - subdirectories named after services <app_name> as set in dockerbuild.cfg
      (one directory per service)
    - Dockerfile: dockerbuild/<app_name>/Dockerfile
    - docker-compose file: ../docker-compose.yml

Examples (run from build dir):

  # Build docker image silently
  %(prog)s

  # Build docker image verbosly
  %(prog)s -v

  # Build docker image and push the image to the registry given in config file
  %(prog)s -p
'''

import argparse
import textwrap
import sys
import os
import re
import json
from config import Config

# useful doc: http://docker-py.readthedocs.io/en/2.0.0/images.html
try:
    import docker
except:
    print "[ERROR] Failed to load docker module. Try: sudo pip install docker"
    sys.exit(1)

def setup_config(name="dockerbuild"):
	return Config(name)


def open_file(filename):
    try:
        with open(filename, 'r') as file :
            return file.read()
    except:
        print "[ERROR] Failed to open file: %s" % filename
        sys.exit(1)


def write_file(filename, content):
    try:
        with open(filename, 'w') as file:
            file.write(content)
    except:
        print "[ERROR] Failed to write file: %s" % filename
        sys.exit(1)


def get_docker_client():

    return docker.DockerClient(base_url='unix:///var/run/docker.sock', version="auto")
    # .from_env() did not work on RHEL7 machines
    #return docker.from_env()


def test_docker_client():

    client = get_docker_client()

    try:
        client.containers.list()

    except Exception as err:
        if "client is newer than server" in err:
            print "[WARNING] Client/Server API version mismatch."
        else:
            print "[ERROR] Failed to instantiate docker client. %s \n        Maybe you are using docker-py module. Try install docker module: sudo pip install docker" % err
            sys.exit(1)


def get_existing_versions(tag_preamble, app_name, image_version):
    client = get_docker_client()

    versions = []
    search_pattern = tag_preamble + "/" + app_name + ":" + image_version
    if args.debug: print "[DEBUG] version search_pattern: %s" % search_pattern

    for image in client.images.list():
        for tag in image.tags:
            if search_pattern in tag:
                version = tag.split(":")[-1]
                if version == "latest":
                    print "[WARNING] You should avoid using 'latest' tag. Ignoring image %s" % tag
                else:
                    versions.append(version)

    versions.sort()
    if args.debug: print "[DEBUG] versions: %s" % str(versions)
    return versions


def build_image(build_dir, tag="", build_args=""):
    client = get_docker_client()

    if args.debug: print "[DEBUG] build parameter: path=%s; tag=%s; build_args=%s" % (build_dir, tag, str(build_args))

    try:
        # building with build-args does not work:
        #   docker.errors.APIError: 500 Server Error: Internal Server Error ("json: cannot unmarshal array into Go value of type map[string]*string")
        #   This is caused by an issue in Go 1.8
        # built_image = client.images.build(path=build_dir, tag=tag, nocache=True, buildargs=build_args)
        built_image = client.images.build(path=build_dir, tag=tag, nocache=True)
        if args.verbose or args.debug: print "[INFO] build OK: %s" % str(built_image)

    except Exception as err:
        print "[WARNING] Build of %s FAILED. %s" % (image_tag, err)


def push_image(tag, insecure_registry):
    client = get_docker_client()

    if args.debug: print "[DEBUG] push parameter: tag=%s; insecure_registry=%s" % (tag, str(insecure_registry))

    try:
        client.images.push(tag, insecure_registry=insecure_registry)
        if args.verbose or args.debug: print "[INFO] push OK"

    except Exception as err:
        print "[WARNING] Push of %s FAILED. %s" % (tag, err)


def replace_string_in_file(filename, search_str, replace_str):
    filedata = open_file(filename)

    filedata = filedata.replace(search_str, replace_str)

    write_file(filename, filedata)


def replace_line_in_file(filename, search_exp, replace_str):
    if args.debug: print "[DEBUG] replace_line_in_file parameter: filename=%s; search_exp=%s; replace_str=%s" % (filename, search_exp, replace_str)

    filedata = open_file(filename)

    filedata = re.sub(search_exp, replace_str, filedata, flags=re.M)

    write_file(filename, filedata)


def replace_image_in_compose(filename, service, tag):
    filedata = open_file(filename)

    replace_mode = 0
    new_filedata = []

    for line in filedata.splitlines():
        if re.match('^#', line):
            new_filedata.append(line)
            continue

        if service in line and replace_mode == 0:
            replace_mode = 1
            new_filedata.append(line)
            continue

        if replace_mode == 1 and re.match('^\s*image:', line):
            line = "    image: " + tag
            replace_mode = 2

        new_filedata.append(line)

    write_file(filename, '\n'.join(new_filedata))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
		prog="dockerbuild",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=DESC,
		epilog=textwrap.dedent(EPILOG)
	)
    parser.add_argument("-p", "--push", help="Push image to registry after build", action='store_true')
    parser.add_argument("-c", "--config", type=str, help="Dockerbuild config file", default="dockerbuild.cfg")
    parser.add_argument("-d", "--debug", help="Debugging", action='store_true')
    parser.add_argument("-v", "--verbose", help="Verbose output", action='store_true')

	# parse the args and call the appropriate command function
    args = parser.parse_args()

    cfg = setup_config()
    cfg.load_config(args.config)

    test_docker_client()

    for service in cfg.services:
        build_args = []
        dockerfile = os.getcwd() + "/" + service['app_name'] + "/Dockerfile"

        if not os.path.isfile(dockerfile):
            print "[ERROR] Dockerfile not found: %s\n        Please create directory structure according to dockerbuild.cfg: dockerbuild/<app_name>/Dockerfile" % dockerfile
            sys.exit(1)

        # get version number from previous builds
        versions = get_existing_versions(cfg.tag_preamble, service['app_name'], service['app_version'])
        if versions:
            if args.verbose or args.debug: print "[INFO] latest version found: %s/%s:%s" % (cfg.tag_preamble, service['app_name'], versions[-1])
            try:
                build_count = int(versions[-1].split("-")[-1]) + 1
            except:
                build_count = 1
            build_release = service['app_version'] + "-" + str(build_count)
        else:
            build_release = service['app_version'] + "-1"

        # compose new tag
        image_tag = cfg.tag_preamble + "/" + service['app_name'] + ":" + build_release
        if args.verbose or args.debug: print "[INFO] new build release tag: %s" % image_tag

        # cram the build-args & prepare Dockerfile
        build_args.extend([cfg.tag_preamble, cfg.maintainer])
        for item in service:
            build_args.append(item.upper()+"="+service[item])
            replace_string_in_file(dockerfile, "$"+item.upper()+"$", service[item])

        replace_line_in_file(dockerfile, r"^MAINTAINER.*", "MAINTAINER "+cfg.maintainer)
        replace_line_in_file(dockerfile, r"^FROM.*", "FROM "+service['from_image']+":"+service['from_image_version'])

        # build [and push] the image
        if args.push:
            image_tag = cfg.registry + "/" + image_tag
            build_image(os.getcwd()+"/"+service['app_name'], image_tag)
            push_image(image_tag, cfg.insecure_registry)
        else:
            build_image(os.getcwd()+"/"+service['app_name'], image_tag)

        # adjust docker-compose.yml
        docker_compose_file = os.pardir + "/docker-compose.yml"
        if os.path.isfile(docker_compose_file):
            replace_image_in_compose(docker_compose_file, service['app_name'], image_tag)
        else:
            print "[WARNING] %s not found" % docker_compose_file

sys.exit(0)
