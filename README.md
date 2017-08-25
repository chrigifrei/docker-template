# Docker Template

Template to build and run a docker image.

For the build of docker images we use a single build script per service entity. A service entity consists of 1 to n services.

Benefits:
- ready for automated builds
- docker-compose files easily converts into kubernetes services files
- docker-compose service entities are ready for scaling
- use standard for versioning images
- simplified push process


### To Do
- Check private registry whether an image of <app_name> is available
- Check syntax on configfile load
- Test CI/CD integration


### Structure

```bash
docker-template               # replace with your service entity name
  │
  ├── docker-compose.yml      # contains the docker run instructions for the whole service entity
  │
  └── dockerbuild
       ├── dockerbuild.cfg    # configure your service entity here
       ├── dockerbuild.py     # buildscript
       ├── config.py          # renders configfile
       ├── busybox-bar        # service: named according to related <app_name> in dockerbuild.cfg
       └── nginx-foo          # service: named according to related <app_name> in dockerbuild.cfg
```

### Requirements

Python docker module

Installation:
```bash
# Make sure pip is installed
yum install -y python-pip     # RHEL
apt install -y python-pip     # Ubuntu

# Install python docker module
pip install docker
```

## BUILD

Store all files/directories needed for the build of the docker image in the `dockerbuild/<app_name>` folder.


dockerbuild.cfg explained

```
{
  "globals":[
    {
      "registry":          "localhost:5000",           # Private on premise registry
      "insecure_registry": "True",                     # http:// instead of https://
      "tag_preamble":      "apontis.ch",               # image name preamble e.g.: apontis.ch/nginx-foo
      "maintainer":        "APONTIS <info@apontis.ch>"
    }
  ],
  "services":[                                         # service entity consisting of all relevant services
    {
      "from_image":         "nginx",                   # Will be put in the FROM line of Dockerfile
      "from_image_version": "1.13.3",                  # Will be put in the FROM line of Dockerfile
      "app_name":           "nginx-foo",               # The name of your app; will be used as docker image name
      "app_version":        "1.13.3-0.1",              # Version of your app; e.g. from_image_version-your_version
      "app_description":    "Lightweight Webserver"
    },
    {
      "from_image":         "busybox",                 # Will be put in the FROM line of Dockerfile
      "from_image_version": "1.27.1",                  # Will be put in the FROM line of Dockerfile
      "app_name":           "busybox-bar",             # The name of your app; will be used as docker image name
      "app_version":        "1.27.1-0.2",              # Version of your app; e.g. from_image_version-your_version
      "app_description":    "Basic Linux"
    }
  ]
}
```


Start the build from `dockerbuild` directory

```bash
./dockerbuild.py --help
```


## RUN

Use always a `docker-compose.yml` file for run instructions.

```bash
cd /place/of/docker-compose.yml
docker-compose up -d
```
