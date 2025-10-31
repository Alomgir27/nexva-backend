#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║    Chrome/ChromeDriver Fix Script      ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Install Chrome
echo "📦 Installing Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt-get update -qq
    apt-get install -y /tmp/google-chrome.deb
    rm -f /tmp/google-chrome.deb
    echo "   ✅ Chrome installed"
else
    echo "   ✅ Chrome already installed"
fi

# Install Chrome dependencies
echo ""
echo "📦 Installing Chrome dependencies..."
apt-get install -y \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libappindicator3-1 \
    libgbm1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xdg-utils

echo "   ✅ Dependencies installed"

# Clean ChromeDriver cache
echo ""
echo "🧹 Cleaning ChromeDriver cache..."
rm -rf /root/.wdm/
echo "   ✅ Cache cleared"

echo ""
echo "✅ Fix complete! Try scraping again."
echo ""

