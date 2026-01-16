# Lambda Container Image with Chrome for Selenium
FROM public.ecr.aws/lambda/python:3.9

# Install Chrome dependencies and tools
RUN yum install -y \
    atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    alsa-lib \
    at-spi2-atk \
    at-spi2-core \
    libdrm \
    libgbm \
    libxkbcommon \
    mesa-libgbm \
    nss \
    nspr \
    xorg-x11-fonts-100dpi \
    xorg-x11-fonts-75dpi \
    xorg-x11-fonts-cyrillic \
    xorg-x11-fonts-misc \
    xorg-x11-fonts-Type1 \
    xorg-x11-utils \
    wget \
    unzip \
    jq \
    && yum clean all

# Use a specific Chrome version known to work with Lambda
# Chrome 119 is stable and works well with Lambda
ENV CHROME_VERSION=119.0.6045.105

# Install Chrome for Testing (headless optimized)
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
    && unzip -q chrome-linux64.zip \
    && mv chrome-linux64 /opt/chrome \
    && chmod +x /opt/chrome/chrome \
    && rm -f chrome-linux64.zip \
    && ln -s /opt/chrome/chrome /usr/bin/google-chrome

# Install matching ChromeDriver
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip -q chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /opt/chromedriver \
    && chmod +x /opt/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64 \
    && /opt/chromedriver --version

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY src/ ${LAMBDA_TASK_ROOT}/

# Set environment variables
ENV CHROME_BIN=/opt/chrome/chrome
ENV CHROMEDRIVER_PATH=/opt/chromedriver

CMD ["handler.lambda_handler"]
