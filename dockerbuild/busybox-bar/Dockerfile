# Change <VALUE> and $VALUE$ in dockerbuild.cfg
FROM <FROM_IMAGE>:<FROM_IMAGE_VERSION>

MAINTAINER <MAINTAINER>

# See dockerbuild.cfg for version numbers
ARG APP_VERSION=""
ARG APP_DESCRIPTION=""

LABEL app.version="$APP_VERSION$" \
      description="$APP_DESCRIPTION$"

# Force encoding
ENV LANG=en_US.utf8

########################
# Your RUN block here
# RUN cmd1 && \
#     cmd2
########################

# Expose the data directory as a volume
VOLUME /data
# Declare it as WORKDIR so that a host mounted volume gets the correct permissions set.
WORKDIR /data

ADD docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
