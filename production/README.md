# LUMINEX · 3D 영상 원본

2035년 포항의 AI 스마트 윈도우를 소개하는 15장면, 150초 영상입니다. Blender 4.3.2, FFmpeg, Python 3.12, Pillow, NumPy, OpenEXR, OpenColorIO와 Intel Open Image Denoise 2.5.1을 사용합니다. 한국어 글꼴은 Noto Sans CJK입니다.

`architecture.py`는 왼쪽·오른쪽·뒤쪽 벽과 창문 주변 벽, 천장·몰딩·간접조명을 구성합니다. 카메라는 실내에 있으며, 자동 개폐 장면에서는 창문 전체가 화면 안에 들어오고 아래 프레임이 자막 위에 보이도록 잡았습니다. 창문에는 샴페인색 알루미늄 프로파일, 고무 실링, 복층 유리와 스페이서, 매립형 손잡이, 센서, 상태 표시등, 배수 홈과 잠금 볼트를 추가했습니다. 유리와 네 방향 프레임, 손잡이는 하나의 개폐 그룹으로 움직입니다. 제품 소개 장면은 손잡이에서 시작해 창문 전체를 보여주는 카메라 이동을 사용합니다.

`character.py`는 피부·의상 텍스처와 노멀맵을 가진 Microsoft Rocketbox 캐릭터, 동봉된 인체 동작을 사용합니다. 보행은 뒤꿈치 착지와 발끝 밀어내기의 회전 중심, 발의 부드러운 이동 곡선, 앞으로 굽히는 무릎 IK와 실제 발바닥 높이를 함께 보정합니다. 학생은 약 1.24m를 네 걸음으로 이동한 뒤 2.5초에 멈춥니다. 제자리에서 걷는 루프를 계속 재생하지 않습니다. 침대에서는 다리를 유지한 채 상체가 일어나며, 이불은 몸의 높이에 여유를 더한 표면을 사용합니다.

`rain.py`는 배경을 국소적으로 변형하는 렌즈 모양 물방울, 유리를 따라 흐르는 물길, 깊이와 길이가 다른 창밖의 빗줄기를 합성합니다. Blender의 물체 인덱스 마스크로 벽·가구·사람을 가리고, 물방울의 위치는 실제 움직이는 유리 좌표를 따릅니다. 비 때문에 방 전체에 푸른 필터를 덧씌우지 않습니다. 태풍 장면은 같은 포항 해안의 별도 `storm.png`를 사용하며, 먹구름·빗줄기·흰 포말과 거친 바다가 나타납니다. 자동 환기·강우 장면과 태풍 장면은 서로 다른 3D 촬영본입니다.

`scene.py`는 Cycles CPU로 렌더링하고 알베도·법선 안내 정보를 이용한 OIDN 처리 뒤 Blender AgX 색상을 적용합니다. 3D 원본은 1280×720이며, 최종 영상과 자막은 1920×1080, 24fps입니다. 보행 구간은 원본 24fps로 렌더링합니다. 학생이 걷기를 마친 3초 이후의 동작은 12fps 원본을 보간합니다. 정적인 실내 휴식 두 촬영본은 6fps, 다른 원본은 주로 12fps로 렌더링하고 움직임을 보간합니다. 취침 호흡은 약 3.9초의 47프레임 루프를 사용합니다. 개폐 장면에서 3D 상태가 같은 프레임은 재사용하며, 비와 유리 화면은 계속 24fps로 움직입니다.

`hud.py`는 투명한 화면 등장, 예보 전환, 그래프와 일정 스크롤을 만듭니다. `composite.py`는 3D 유리 좌표에 화면을 투시 합성하고 손가락 가림을 적용합니다. 야외 원격 제어는 3D 인물·접촉 그림자를 캠퍼스 이미지에 합성하고 집 안 창문의 실제 촬영본을 LIVE 화면으로 보여줍니다. 닫힘 뒤에는 유리 영역만 암흑 모드로 바뀝니다. 해안·캠퍼스 이미지와 광학 효과는 미래 제품 콘셉트의 시각적 표현입니다.

Linux x86-64에서 Blender, FFmpeg, Noto Sans CJK를 설치한 뒤 실행합니다. 런타임 설치에는 네트워크 연결이 필요하며 바이너리는 Git에 포함하지 않습니다.

```sh
python production/setup_runtime.py

# 보행 한 프레임: 원본 24fps
LUMINEX_PYTHON="$(command -v python)" LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
blender -b -t 1 --factory-startup --python-exit-code 1 \
  --python production/scene.py -- --scene 5 --sample 24 --fps 24 --width 1280 --samples 4

# 11개의 3D 촬영본 + 도시 오프닝·엔딩 → 전체 15장면
python production/build.py
python production/verify_media.py
python production/verify_motion.py
```

모델·공간·카메라를 바꾼 뒤 다시 만들 때는 해당 촬영본의 `raw/`, `frames/`, `masters/`, `clips/`와 `camera_XX.json` 캐시를 지우고 재생성합니다. 보행의 24fps 프레임과 원본 시간을 유지하도록 `build.py`가 구간별 보간과 편집을 처리합니다. 장면 전환은 4프레임 디졸브이며 10초 경계와 총 150초 길이를 유지합니다.

`assets/soundtrack.m4a`의 한국어 내레이션(M3), 별도 창문 안내(F1), 잔잔한 피아노 음악은 이번 시각 수정에서 그대로 유지했습니다. 제품 이름은 LUMINEX(루미넥스)입니다. `storyboard.json`은 장면 구성, `speech_segments.json`은 음성별 자막 타이밍입니다. 자산 출처는 `ATTRIBUTION.md`와 `licenses/`에 있습니다.

출력은 `output/LUMINEX_Pohang_2035.mp4`와 `output/AI_Smart_Window_Pohang.mp4`에 동일하게 저장합니다. `verify_media.py`는 MP4 헤더·길이·프레임 수·두 파일의 체크섬과 전체 디코딩을 검사합니다. `verify_motion.py`는 렌더링할 때 생성하는 `camera_XX.json`을 사용해 이동과 정지 후 발 위치, 바닥 및 이불 간격을 검사합니다.
