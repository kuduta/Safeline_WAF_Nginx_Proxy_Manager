# SafeLine WAF + Nginx Proxy Manager

สภาพแวดล้อมทดสอบ WAF บน Docker พร้อมเว็บตัวอย่าง สำหรับเปรียบเทียบ request
ที่เข้าต้นทางโดยตรง ผ่าน NPM และผ่าน SafeLine

**เครื่อง Windows/Docker Desktop นี้ต้องใช้ docker-compose.desktop.yml ร่วมกับไฟล์หลัก**
เพื่อเข้าถึง WAF ที่พอร์ต 80 ไม่ต้องเปิด host networking ใน Docker Desktop
ชุด Desktop เปิดเฉพาะ HTTP บน localhost สำหรับทดสอบ ยังไม่ใช่การตั้งค่า HTTPS สำหรับ production

## เริ่มใช้งานระบบที่ติดตั้งไว้แล้ว

เปิด PowerShell ในโฟลเดอร์โครงการ แล้วกำหนดรายการไฟล์ Compose สำหรับ terminal นี้:

```powershell
Set-Location 'C:\path\to\Safeline_WAF_Nginx_Proxy_Manager'
$composeArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.desktop.yml', '--profile', 'test')
docker compose @composeArgs config --quiet
docker compose @composeArgs up -d
docker compose @composeArgs ps
```

หากเปิด terminal ใหม่ ต้องกำหนด $composeArgs อีกครั้ง
อย่าใช้ไฟล์หลักเดี่ยวเพื่อ up/recreate บนเครื่องนี้ เพราะจะเปลี่ยน Tengine กลับเป็น host networking

| URL | หน้าที่ | ผ่าน WAF |
| --- | --- | --- |
| [https://localhost:9443](https://localhost:9443) | SafeLine UI: เว็บไซต์ กฎ และเหตุการณ์ | หน้าจัดการ |
| [http://localhost:81](http://localhost:81) | NPM UI: Proxy Hosts | หน้าจัดการ |
| [http://waf-test.localhost](http://waf-test.localhost/) | เว็บทดสอบผ่าน SafeLine และ NPM | ใช่ |
| [http://waf-test.localhost:8080](http://waf-test.localhost:8080/) | เว็บผ่าน NPM อย่างเดียว | ไม่ผ่าน |
| [http://localhost:18080](http://localhost:18080/) | ต้นทางโดยตรง สำหรับ baseline | ไม่ผ่าน |

พอร์ตที่ publish ในชุด Desktop จำกัดไว้ที่ 127.0.0.1 จึงเข้าได้จากเครื่องนี้
ฐานข้อมูลไม่ได้ publish พอร์ตออกมาที่ host

## โครงสร้างและเส้นทาง request

```text
Windows browser: http://waf-test.localhost:80
  -> Tengine / SafeLine WAF (Docker bridge, published localhost:80)
  -> private relay 127.0.0.1:8080 ภายใน network namespace ของ Tengine
  -> Nginx Proxy Manager:80
  -> test-site:8080
```

ค่า backend ของเว็บไซต์ใน SafeLine ยังคงเป็น http://127.0.0.1:8080
บน Desktop ค่านี้หมายถึง relay ภายใน Tengine ส่วนบน Linux แบบ host networking
หมายถึงพอร์ต NPM ที่ publish บน loopback ของ Linux host

| กลุ่ม | Services |
| --- | --- |
| SafeLine | postgres, mgt, detect, tengine, luigi, fvm, chaos |
| NPM | npm-app, npm-db |
| เว็บตัวอย่าง (profile test) | test-site, test-route-init |
| เพิ่มสำหรับ Desktop | waf-upstream-relay |

ไฟล์หลักเปิด 9 services โดยปริยาย; profile test เพิ่มเว็บและตัวเตรียม route แบบ one-shot
เมื่อรวม Desktop + profile test มี 12 services: 11 ตัวรันต่อเนื่อง และ test-route-init จบด้วย exit 0
เฉพาะบาง services มี healthcheck คำว่า running ของบริการอื่นไม่ได้ยืนยันทุกฟังก์ชันภายใน

## บัญชีเข้าใช้งาน

### SafeLine

Username เริ่มต้นคือ **admin** ไม่มี password กลางที่ใช้ได้กับทุกการติดตั้ง
หากยังไม่ได้ตั้งบัญชี หรือจำรหัสไม่ได้ ใช้:

```powershell
docker compose @composeArgs exec mgt resetadmin
```

คำสั่งนี้ **สร้าง/รีเซ็ตรหัสผ่าน admin** และแสดงค่าใหม่ใน terminal
ไม่ใช่คำสั่งดูรหัสเดิม เก็บค่าไว้เป็นความลับ แล้วเข้า https://localhost:9443/login
รหัส POSTGRES_PASSWORD ใน .env เป็นรหัสฐานข้อมูล ไม่ใช่รหัสเข้า UI

### Nginx Proxy Manager

เข้า http://localhost:81 แล้วทำขั้นตอนตั้งบัญชีครั้งแรกที่ UI แสดง
หากตั้งบัญชีไปแล้ว ให้ใช้บัญชีนั้น รหัส NPM_DB_PASSWORD ใน .env ไม่ใช่รหัสเข้า UI

## ตั้งค่าและทดสอบเว็บไซต์ผ่าน WAF

### 1. ตั้งเว็บไซต์ใน SafeLine

ในหน้า Websites/Applications เพิ่มเว็บไซต์ หรือแก้รายการเดิม โดยใช้:

| ช่อง | ค่า |
| --- | --- |
| Domain / Server name | waf-test.localhost |
| Protocol | HTTP |
| Listen port | 80 |
| Upstream / Backend | http://127.0.0.1:8080 |
| Host header | คง waf-test.localhost |

บันทึกและเปิดการป้องกันแบบบล็อก หากต้องการทดสอบการปฏิเสธ request
ชื่อเมนูอาจต่างกันตามเวอร์ชัน

NPM มี custom route สำหรับ waf-test.localhost อยู่แล้ว
**อย่าสร้าง Proxy Host ชื่อนี้ซ้ำใน NPM UI**

### 2. เปรียบเทียบสามเส้นทาง

เปิดต้นทาง http://localhost:18080/ แล้วลอง Normal request, SQL injection sample และ XSS sample
ทั้งสามควรถึงต้นทางและได้ HTTP 200 เพื่อใช้เป็น baseline
เว็บนี้คืน input เป็น JSON เท่านั้น ไม่มีฐานข้อมูล การ execute SQL หรือ shell
และแสดง response ผ่าน textContent จึงไม่รัน HTML/script ที่รับกลับมา

จากนั้นเปิด http://waf-test.localhost/ โดยไม่มี :8080 แล้วกดปุ่มเดิม

| Request | ผลที่ตรวจ |
| --- | --- |
| Normal request | HTTP 200 และ origin เป็น waf-test-site |
| SQL injection sample | ตรวจพบ/บล็อกตามนโยบาย SafeLine |
| XSS sample | ตรวจพบ/บล็อกตามนโยบาย SafeLine |

เปิด Attack Logs/รายการเหตุการณ์ของ SafeLine เลือกเว็บไซต์และเวลาล่าสุด
ตรวจ URL /api/echo, ประเภทเหตุการณ์ และผล Allowed/Blocked
HTTP status อย่างเดียวไม่ยืนยันสาเหตุการบล็อก

### 3. ทดสอบจาก PowerShell

ใช้ curl.exe เพื่อไม่ให้สับสนกับ alias ของ Windows PowerShell

```powershell
# ต้นทางโดยตรง
curl.exe --noproxy '*' http://localhost:18080/health

# ผ่าน NPM อย่างเดียว
curl.exe --noproxy '*' -H 'Host: waf-test.localhost' http://127.0.0.1:8080/health

# request ปกติผ่าน WAF
curl.exe --noproxy '*' -i 'http://waf-test.localhost/api/echo?q=hello-world'

# SQL injection ตัวอย่างไปยังเว็บทดสอบของเรา
curl.exe --noproxy '*' -i --get --data-urlencode "q=1' OR '1'='1' --" http://waf-test.localhost/api/echo

# XSS ตัวอย่าง
curl.exe --noproxy '*' -i --get --data-urlencode 'q=<script>alert(1)</script>' http://waf-test.localhost/api/echo
```

ผลที่ตรวจจริงเมื่อ 29 ตุลาคม 2026 บนเครื่องนี้:
หน้าเว็บผ่าน WAF และ normal request ได้ HTTP 200; SQL injection ตัวอย่างได้ HTTP 403
ผลนี้ไม่ใช่การรับรองว่าทุกกฎหรือทุก payload จะถูกบล็อก

## ติดตั้งใหม่จากไฟล์โครงการ

ต้องมี Docker Engine แบบ Linux/amd64 หรือ Docker Desktop ใช้ Linux containers
และ Docker Compose 2.24.4+ สำหรับ !reset / !override
ตรวจพอร์ต 80, 81, 8080, 9443 และ 18080 ไม่ให้ชนบริการอื่น

### เตรียม .env

เครื่องนี้มี .env พร้อมรหัสสุ่มแล้ว **อย่าสร้างทับหากมีข้อมูลฐานข้อมูลอยู่**
สำหรับเครื่องใหม่ คัดลอก .env.example เป็น .env แล้วกรอกค่าต่อไปนี้ด้วย random hex
อย่างน้อย 32 bytes โดยใช้คนละค่ากัน:

- POSTGRES_PASSWORD
- NPM_DB_PASSWORD
- NPM_DB_ROOT_PASSWORD
- MGT_INTERNAL_TOKEN
- DETECTOR_MGMT_TOKEN

ตัวอย่างสร้างค่าเดียวด้วย PowerShell 7:

```powershell
$secretBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($secretBytes)
[Convert]::ToHexString($secretBytes).ToLowerInvariant()
```

รันแยกสำหรับแต่ละค่า POSTGRES_PASSWORD ต้องปลอดภัยสำหรับ connection URI จึงแนะนำ hex
ตรวจ SUBNET_PREFIX ไม่ให้ชน LAN/VPN/Docker networks ค่าเริ่มต้นคือ 172.22.222.0/24
SAFELINE_DIR=./safeline เป็น path เทียบกับโฟลเดอร์ Compose
เก็บ .env เป็นความลับ; .gitignore ไม่ได้แทนการตั้งสิทธิ์ไฟล์
อย่าแชร์ผล docker compose config แบบเต็ม เพราะมีรหัสผ่านที่ resolve แล้ว

### เตรียม custom route ของ NPM อัตโนมัติ

ใช้ --profile test ตอน up ตัว test-route-init จะสร้าง/เพิ่ม route จาก test-site/npm.conf
ลง npm/data/nginx/custom/http.conf ก่อน NPM เริ่ม โดยเก็บ config อื่นและไม่เพิ่มโดเมนซ้ำ
ถ้ามี config เดิมจะสำรองครั้งแรกไว้ใน http.conf.before-test-route
ไฟล์ใช้งานจริงเขียนได้เพื่อให้ NPM เปลี่ยน ownership ได้ระหว่าง startup

```powershell
docker compose @composeArgs up -d
```

ติดตั้งใหม่ไม่ต้องคัดลอก custom route เอง แต่ยังต้องเพิ่มเว็บไซต์ใน SafeLine
การไม่เปิด profile ไม่ได้ลบ test route ที่เคยติดตั้งไว้ หรือหยุด test container ที่รันอยู่แล้ว
ก่อนเปลี่ยนเป็น production ให้หยุด test-site และลบ server block ของ waf-test.localhost
จาก custom config โดยเก็บ config อื่นไว้ แล้วตรวจ nginx -t และ reload NPM

### Linux Docker Engine โดยตรง

ใช้ docker-compose.yml โดยไม่รวม Desktop override:

```sh
chmod 600 .env
docker compose config --quiet
docker compose pull
docker compose --profile test up -d
docker compose --profile test ps
```

Tengine ใช้ host networking ตามโครงสร้าง upstream; UI และ NPM ยัง bind loopback
หากเข้า UI จากเครื่องอื่น ใช้ SSH tunnel:

```sh
ssh -L 9443:127.0.0.1:9443 -L 8181:127.0.0.1:81 user@server
```

เปิด SafeLine ที่ https://localhost:9443 และ NPM ที่ http://localhost:8181
การเปิดรับ HTTPS ของเว็บไซต์จริงต้องตั้ง certificate และ listener ใน SafeLine เพิ่ม
Desktop override ปกติไม่ได้ publish 443; มีไฟล์เสริม docker-compose.desktop.https.yml
สำหรับ publish 127.0.0.1:443 หลังตั้ง HTTPS listener และ certificate ใน SafeLine แล้ว

## คำสั่งดูแลระบบบน Desktop

ใช้ $composeArgs ที่กำหนดไว้ตอนเริ่มต้น:

```powershell
# สถานะ และ log ล่าสุด
docker compose @composeArgs ps
docker compose @composeArgs logs --tail 100 mgt tengine npm-app test-site

# ดู log ต่อเนื่อง ออกด้วย Ctrl+C
docker compose @composeArgs logs -f --tail 100

# หยุด/เปิดกลับ โดยเก็บข้อมูล
docker compose @composeArgs stop
docker compose @composeArgs start

# ตรวจ config แล้วใช้การเปลี่ยนแปลง
docker compose @composeArgs config --quiet
docker compose @composeArgs up -d
```

เมื่อ recreate Tengine โดยเจาะจง ให้รวม waf-upstream-relay ด้วย
เพราะ relay แชร์ network namespace ของ Tengine:

```powershell
docker compose @composeArgs up -d --force-recreate tengine waf-upstream-relay
```

การอัปเกรด: สำรองข้อมูล ตรวจ release notes และทดสอบ restore/compatibility ก่อน
จากนั้นปรับ pinned versions แล้ว pull/up ด้วยไฟล์ Compose ชุดเดิม

## แก้ปัญหาที่พบบ่อย

| อาการ | จุดตรวจ/วิธีแก้ |
| --- | --- |
| เข้า waf-test.localhost พอร์ต 80 ไม่ได้ แต่ :8080 ได้ | ใช้ Desktop override แล้วตรวจ ps ว่า Tengine publish 127.0.0.1:80 |
| ชื่อ waf-test.localhost resolve ไม่ได้ | ทดลอง curl.exe -H 'Host: waf-test.localhost' http://127.0.0.1/; หากจำเป็นเพิ่ม hosts entry 127.0.0.1 waf-test.localhost ด้วยสิทธิ์ผู้ดูแล |
| Port already in use | ตรวจ Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue และ containers ที่ publish พอร์ต อย่าหยุดบริการอื่นก่อนระบุเจ้าของ |
| ได้ 502 | ตรวจ test-site, npm-app, waf-upstream-relay และ backend/Host header ใน SafeLine |
| ทุก payload ได้ 200 | ตรวจว่าเปิด URL พอร์ต 80 และเว็บไซต์อยู่โหมดบล็อก ไม่ใช่ monitor |
| NPM ได้ Empty reply | ตรวจ logs npm-app และ nginx -t; config แบบ read-only ใน conf.d เคยทำให้ startup ล้มเหลว |
| SafeLine UI เข้าไม่ได้ | ตรวจ mgt/postgres health และ logs; HTTPS ของ UI อาจใช้ certificate ที่เบราว์เซอร์ยังไม่เชื่อถือ |
| แก้ password ใน .env แล้ว DB เข้าไม่ได้ | Environment ไม่เปลี่ยน password ของฐานที่ initialize แล้ว ต้องเปลี่ยนในฐานให้ตรงกัน |

ตรวจ Nginx ของทั้งสองระบบ:

```powershell
docker compose @composeArgs exec tengine nginx -t
docker compose @composeArgs exec npm-app nginx -t
```

## Log และ Splunk

ค่าเริ่มต้นใช้ Docker local logging หมุนไฟล์ 20 MB x 5 ต่อ container
ไม่ครอบคลุม application logs ใน safeline/logs/ และ npm/data/logs/
ให้ตั้ง retention/logrotate หรือ collector สำหรับไฟล์เหล่านี้แยก

ตั้งปลายทางใน .env โดยแทน ip syslog ด้วย IP หรือ hostname จริงก่อนใช้งาน:

```dotenv
SYSLOG_ADDRESS=tcp://ip syslog:514
```

บน Desktop ต้องรวมไฟล์ทั้งสี่เพื่อส่ง log ของ relay ด้วย และใช้ชุดนี้ต่อเนื่อง:

```powershell
$composeArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.desktop.yml', '-f', 'docker-compose.syslog.yml', '-f', 'docker-compose.desktop.syslog.yml', '--profile', 'test')
docker compose @composeArgs config --quiet
docker compose @composeArgs up -d
```

บน Linux host ใช้ไฟล์หลักกับ syslog override สองไฟล์
syslog override ส่ง stdout/stderr ของ services หลักและ test profile;
desktop.syslog override เพิ่ม relay ให้ใช้ syslog เช่นกัน
ตรวจ TCP listener ให้เข้าถึงได้ก่อน up เพราะ Docker syslog driver อาจเริ่มไม่ได้
หากปลายทางไม่พร้อม แม้ตั้ง non-blocking ไว้แล้วก็ตาม
buffer non-blocking 4 MB อาจทำ log หายเมื่อเต็ม
ถ้าต้องการความทนทาน ให้ใช้ collector ที่มี persistent disk queue
access/WAF events ที่อยู่ในไฟล์ต้องตั้ง collector เพิ่มและยืนยันตำแหน่งจากเวอร์ชันที่รัน
หากใช้ TLS ต้องตั้ง syslog listener, certificates และ Docker TLS options ให้ครบ

## ข้อมูลถาวร การสำรอง และย้ายระบบ

| ตำแหน่ง | ข้อมูล |
| --- | --- |
| safeline/resources/postgres/data | PostgreSQL ของ SafeLine |
| safeline/resources/mgt | ข้อมูล management |
| safeline/resources/nginx, detector, chaos, luigi | ข้อมูลและ config ของ SafeLine |
| safeline/resources/sock, run | runtime sockets ไม่ควรนำ sockets เก่าไป restore |
| safeline/logs | log ที่เขียนลงไฟล์ |
| npm/mysql | MariaDB ของ NPM |
| npm/data | ข้อมูล NPM และ custom route |
| npm/letsencrypt | certificates ของ NPM |
| .env | รหัสผ่านและ token |

ก่อน backup แบบคัดลอกไฟล์ ให้ stop ทั้ง stack ด้วย Compose ชุดที่ใช้อยู่
คัดลอก .env, Compose ทุกไฟล์ที่ใช้, test-site/, safeline/ และ npm/ ไป backup
โดยไม่เก็บ runtime socket files จาก resources/sock และ resources/run
ตรวจความสำเร็จแล้ว start กลับ แม้ backup ล้มเหลวก็ควรเปิดบริการกลับตามแผน
backup มีรหัสผ่าน/private keys ให้จำกัดสิทธิ์ เข้ารหัส และเก็บสำเนานอกเครื่อง

การย้าย Windows bind mounts ไป Linux หรือเปลี่ยน database image ควรใช้ logical dump/restore
และตรวจ ownership/permissions; อย่าถือว่าการคัดลอก raw datadir ข้ามระบบจะใช้ได้เสมอ
ทดสอบ restore บนเครื่องแยก โดยใช้ Compose/.env/images รุ่นเดียวกับ backup
ตรวจ login UI, DB health, normal request และ WAF block ก่อนสลับ traffic

หากเคยใช้ docker-compose.original.yml: ชื่อ services, PostgreSQL image/user/database
และ path ข้อมูล SafeLine เปลี่ยนแล้ว; MariaDB เปลี่ยนจาก jc21/mariadb-aria เป็น official mariadb
ต้องวางแผน migration บนสำเนาข้อมูลก่อน ห้ามเริ่ม image ใหม่ทับ datadir เดิมโดยไม่ตรวจ compatibility
อย่าใช้ down -v หรือลบ safeline/npm เป็นขั้นตอนอัปเกรด

## เพิ่มเว็บไซต์จริง

1. ตั้ง NPM Proxy Host ให้โดเมนจริงส่งไปชื่อ container/IP และพอร์ตของแอป
2. ถ้าแอปอยู่ stack อื่น ต่อ npm-app เข้า network ของแอป หรือใช้ IP ที่เข้าถึงได้
3. เพิ่มโดเมนเดียวกันใน SafeLine ให้ backend เป็น http://127.0.0.1:8080 และคง Host header
4. ให้ SafeLine terminate TLS; ปิด Force SSL ใน NPM สำหรับเส้นทางนี้เพื่อหลีกเลี่ยง redirect วน
5. ตรวจ forwarded scheme/client IP และ trusted proxies ให้ถูกต้องก่อนใช้กฎอิง IP

การเปิดใช้งานอินเทอร์เน็ตต้องออกแบบ bind address, firewall, DNS และ certificates เพิ่ม
ชุด Desktop นี้เปิด localhost เท่านั้น และยังไม่ publish HTTPS
ก่อน production ให้ถอดเว็บ/route ทดสอบและพอร์ต baseline ที่ไม่จำเป็น

## ไฟล์และ pinned versions

| ไฟล์ | หน้าที่ |
| --- | --- |
| docker-compose.yml | ชุดหลักสำหรับ Linux host networking |
| docker-compose.desktop.yml | bridge override และ private relay สำหรับ Desktop |
| docker-compose.syslog.yml | ส่ง container stdout/stderr ไป syslog |
| docker-compose.desktop.syslog.yml | ส่ง log ของ Desktop relay ไป syslog |
| docker-compose.desktop.https.yml | ตัวเลือก publish localhost:443 หลังเตรียม TLS แล้ว |
| .env.example | ตัวอย่างตั้งค่า ไม่มีรหัสใช้งานจริง |
| test-site/server.py, index.html | เว็บทดสอบและ JSON echo |
| test-site/init-route.py | เตรียม NPM test route อัตโนมัติแบบ one-shot |
| test-site/npm.conf | ต้นฉบับ custom route ของ NPM |
| test-site/desktop-relay.conf | relay ภายใน Tengine สำหรับ Desktop |
| docker-compose.original.yml | สำเนาก่อนแก้ อาจมี credentials เดิม อย่านำไปเผยแพร่ |
| safeline-upstream.reference.yml | release Compose ที่ดาวน์โหลดไว้เพื่อเทียบ ไม่ใช่ไฟล์ที่นำมารัน |

SafeLine international 9.3.10, SafeLine PostgreSQL 15.2, NPM 2.16.0,
MariaDB 10.11.14, Python 3.13.9-alpine และ relay Nginx 1.28.0-alpine
เป็นเวอร์ชันที่ pin ไว้ ไม่ได้ยืนยันว่าเป็นรุ่นล่าสุด

Upstream reference ดาวน์โหลดเมื่อ 29 ตุลาคม 2026 จาก
[SafeLine release Compose](https://waf.chaitin.com/release/latest/compose.yaml)
เป็น snapshot วันที่ดาวน์โหลด ไม่รับประกันว่าตรงกับ images 9.3.10 ทุกส่วน



### เปิดพอร์ต HTTPS บน Desktop เมื่อเตรียม TLS แล้ว

เพิ่มเว็บไซต์ HTTPS และ certificate ใน SafeLine ก่อน จากนั้นใช้:

```powershell
$composeArgs = @('-f', 'docker-compose.yml', '-f', 'docker-compose.desktop.yml', '-f', 'docker-compose.desktop.https.yml', '--profile', 'test')
docker compose @composeArgs config --quiet
docker compose @composeArgs up -d
```

ไฟล์นี้ publish เฉพาะ 127.0.0.1:443 ไม่ได้สร้าง certificate หรือ HTTPS listener ให้
หากใช้ Syslog ด้วย ให้เพิ่มไฟล์ syslog ทั้งสองต่อท้ายรายการ -f ก่อน --profile

ก่อนเปิด Syslog ให้เปลี่ยนข้อความตัวอย่าง ip syslog เป็น IP หรือ hostname ของปลายทางจริง
และตรวจว่ารับ TCP พอร์ต 514 ได้ก่อน การเปลี่ยน driver จะ recreate containers
และมีช่วงสะดุดของบริการ


