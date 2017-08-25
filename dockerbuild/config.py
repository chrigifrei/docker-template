''' Dockerbuild Helper Script
Description:
    Loads the config given as arg or using the default (%(prog)s.cfg)
'''

import os, sys
import json


class Config():

    def __init__(self, name):
        self.name = name
        self.me = self.name
        self.file = '%s.cfg' % name


    def load_config(self, configfile):

        try:
            with open(configfile, 'r') as f:
                self.item = json.load(f)
        except Exception as err:
            print '[ERROR] Failed to load config file: %s.' % err
            sys.exit(1)


        # [TODO] 23.08.2017: config param syntax check

        self.registry          = self.item['globals'][0]['registry']
        self.insecure_registry = self.item['globals'][0]['insecure_registry']
        self.tag_preamble      = self.item['globals'][0]['tag_preamble']
        self.maintainer        = self.item['globals'][0]['maintainer']
        self.services          = self.item['services']
