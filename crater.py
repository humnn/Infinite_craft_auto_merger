cookie="_ga=GA1.1.609389273.1748161502; pwBotScore=97; usprivacy=1---; _cc_id=d7550d008358954bcfa8e23c0ab71a67; panoramaId_expiry=1748766315262; panoramaId=109c74dd9ee6f61b394085e76d84185ca02c7e9abe36931758bb5f46a105ae05; panoramaIdType=panoDevice; ad_clicker=false; _sharedid=4f21e646-7258-475b-8161-1746e7ed6e46; _sharedid_cst=zix7LPQsHA%3D%3D; _li_dcdm_c=.neal.fun; _lc2_fpi=edcefc4d0c5f--01jw37bctwendkhn3czmw2r7g9; _lc2_fpi_meta=%7B%22w%22%3A1748160066397%7D; mako_fpc_id=a3d6f0c0-50b4-479e-890a-508ec4afbaf8; cf_clearance=1BG8oBjD7sBhfmbgwSn062TvdrEbkS8S4FOoTjmHj5I-1748166807-1.2.1.1-EID45aBxgRphKhDD_TS_VjnxE7Q6BeJYcPk7HunA6Wi1M_2dAvxeBi85g8Qcx3E.HvGO5mOWSCdB_o8WaH8xEeuGv2u.jbq9W6F5tJMy4U5IHrb8tP4UuGwDTL8nxXDO9d18ZzHk4EXuss3OYXCc0c6weluGJ_8eg5rvMMrqMXDn6aF3zCgY4IaOiE5sHktm87giXHVXmTJYM02Nl668c7PCqDycUWCnyrQDA0oIH1mlMKLVgpZsogrJp4q30bCvxcxObBExj_TVRgPIPwmqaFjMvCBGAICAdlsDazsUfj6Opvvz_P4araW12j_TmB24TEmAYvbmP9PpmV4WiYaErB_QIgsB3YBfWMI2YGjtrPA; __gads=ID=12c24e42a04f1a44:T=1748161524:RT=1748166808:S=ALNI_MYJlMiAo7LLIclndFjkkAymENpcBw; __gpi=UID=000010c6a5afb6dd:T=1748161524:RT=1748166808:S=ALNI_MZAVJko7rDAEPcL4Bg0IJnsZ_kj3w; __eoi=ID=5b6605dfc893eb9e:T=1748161524:RT=1748166808:S=AA-AfjaTPxAx1dUgzMFxRUlRpacO; _ga_L7MJCSDHKV=GS2.1.s1748166790$o2$g1$t1748166809$j0$l0$h0; FCNEC=%5B%5B%22AKsRol_IZVfy4YOw8oiuawFVxbgUEHhP_cSsA8h5cGvMYw1TPvIiSmk8l34RoIykiF0BN7LbMjgScdKTi-FB1ZgHelBSd0XjuwBmmT7jtmjtA9prAsWBV_CxcK9GZpSK1duO1EGhE7YxGZaGwU1i8Ik2x4CeXCTL1w%3D%3D%22%5D%5D; cto_bundle=OoVNIF8xN0hzd25PSlFldWFxOTFlN1lYVTh3b2xkRUh4ZklvRXBhMSUyRjZDRVRWU0xnZXhhbEZLbkVxQkcwbEtpT0FlV2VDVFNmZHdwTDgzY3MlMkJIcXVsZTJTM2RDT0lOeXVCeVNROXVtNSUyRjkzckNTUnNPSFhmZ3k5eGV0dVZ1S2pKTzJFR3RJVzFvTWhTUlVkd204RyUyRnozREtCalVKSUxyTTl1NEMlMkYwTzE5YjBSOU1Rb3glMkIwaHY4NkE0SVJQUG9wUkFNdXVMNmQ1bkx6dmpUOUNqZSUyQlYyck5QQnclM0QlM0Q; cto_bidid=Vi0YSl9Qc2U3bEs3UkZGUEpvSkZIRXpiaU1kdXc4UjMweGF5TFV0Rzl6dWhmaHklMkZxdmF0UDAyc2hTSVowQnJBNnRuMGkxMDFGc0tZVmxjZkM3ZWdjaVZYeUVzZkY5NzNJOENEVlh1S21Qc3g3TDlBJTNE"
import requests
import gzip
import brotli
import json

url = "https://neal.fun/api/infinite-craft/pair?first=Forest&second=Tree"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://neal.fun/infinite-craft/",
    "Origin": "https://neal.fun",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": f"{cookie}"
}

response = requests.get(url, headers=headers)
content_encoding = response.headers.get("Content-Encoding", "")

try:
    if content_encoding == "gzip":
        decompressed_data = gzip.decompress(response.content).decode("utf-8")
    elif content_encoding == "br":
        decompressed_data = brotli.decompress(response.content).decode("utf-8")
    else:
        decompressed_data = response.text

    result = json.loads(decompressed_data)
    print("✅ Result:", result)

except Exception as e:
    print("❌ Error:", e)
    print("Raw response:", response.content[:200])  # Print a snippet to debug
