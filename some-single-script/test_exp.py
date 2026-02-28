from playwright.sync_api import Page, expect,sync_playwright
from main import *


def test_main():
    url="https://store.apple.com/go/jp/vieworder/W1423621117/avz813@yamaguchishoji.com"
    automated_parcel_tracking(url)