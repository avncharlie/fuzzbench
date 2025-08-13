ARG parent_image

FROM grammatech/ddisasm AS ddisasm 

FROM $parent_image

# Install ddisasm and gtirb-pprinter from prebuilt container
COPY --from=ddisasm /lib/x86_64-linux-gnu/libboost_filesystem.so.1.71.0 /lib/x86_64-linux-gnu/libboost_filesystem.so.1.71.0
COPY --from=ddisasm /lib/x86_64-linux-gnu/libboost_program_options.so.1.71.0 /lib/x86_64-linux-gnu/libboost_program_options.so.1.71.0
COPY --from=ddisasm /lib/libcapstone.so.5 /lib/libcapstone.so.5
COPY --from=ddisasm /lib/x86_64-linux-gnu/libgomp.so* /lib/x86_64-linux-gnu/
COPY --from=ddisasm /usr/local/lib/libgtirb.so* /usr/local/lib/
COPY --from=ddisasm /usr/local/lib/libgtirb_layout.so* /usr/local/lib/
COPY --from=ddisasm /usr/local/lib/libgtirb_pprinter.so* /usr/local/lib/
COPY --from=ddisasm /lib/x86_64-linux-gnu/libprotobuf.so* /lib/x86_64-linux-gnu/
COPY --from=ddisasm /usr/local/bin/ddisasm /usr/local/bin/
COPY --from=ddisasm /usr/local/bin/gtirb* /usr/local/bin/
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV DEBIAN_FRONTEND=noninteractive 

# Install the necessary packages.
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        python3.9
# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.9 get-pip.py

# Download latest release of AFL++.
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/v4.32c
# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make

# Install PeAR 
RUN git clone https://github.com/avncharlie/PeAR.git /PeAR
RUN python3.9 -m pip install -r /PeAR/requirements.txt
# Compile PeAR driver
RUN cd /PeAR/utils/pear_driver && make
