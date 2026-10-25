# LUMINEX · 3D 영상 원본

2035년 포항을 배경으로 한 15장면, 150초 영상입니다. Blender 4.3.2, FFmpeg, Python 3.12, Pillow, NumPy, OpenEXR, OpenColorIO와 Intel Open Image Denoise 2.5.1을 사용합니다. 한국어 글꼴은 Noto Sans CJK입니다.

`character.py`는 피부·의상 텍스처가 포함된 Microsoft Rocketbox 캐릭터와 인체 동작을 사용합니다. 피부·옷의 노멀맵과 관절 변형 보정을 적용했습니다. 걷는 동안 발을 공간에 고정하고 이동이 끝나면 걷기를 중단합니다. 이 모델의 허리 아래에 연결된 다리는 별도로 보정해, 상체를 움직여도 발과 다리가 함께 끌려가지 않게 합니다. 침대 이불은 변형된 몸의 높이와 여유 공간을 반영한 매끈한 표면으로 구성합니다.

`scene.py`는 가구·목재·직물·조명을 배치하고 Cycles CPU로 렌더링합니다. 알베도와 법선 정보를 이용한 외부 OIDN 처리 뒤 Blender AgX 색상을 적용합니다. 실내 원본은 1280×720, 12fps이며 움직임을 보간해 1920×1080, 24fps로 출력합니다. 야외 장면은 투명 배경의 3D 인물과 접촉 그림자를 1920×1080 캠퍼스 이미지에 합성합니다. 배경 이미지와 광학 효과는 미래 제품 콘셉트의 시각적 표현입니다.

창문은 유리, 네 방향 프레임, 손잡이를 하나의 개폐 그룹으로 움직입니다. 반투명 모드에서는 같은 좌표의 선명한 외부 이미지와 흐린 이미지를 전환해 색·빛이 남도록 표현합니다. `hud.py`는 투명한 화면의 등장, 주간 예보 전환, 그래프 그리기와 일정 스크롤을 만듭니다. `composite.py`는 3D 창문 좌표에 화면을 투시 합성하며 손가락 가림과 얇은 투명 배경을 적용합니다. 야외 원격 제어 장면에는 집 안 창문의 실제 움직이는 촬영본을 LIVE 미리보기로 표시합니다. 닫힘 뒤 암흑 모드로 바뀔 때는 실제 창문 형상의 가림 마스크를 사용해 앞쪽 가구가 함께 어두워지지 않도록 합니다.

Linux x86-64에서 Blender와 FFmpeg, Noto Sans CJK를 설치한 뒤 실행합니다. 외부 디노이저 설치에는 네트워크 연결이 필요하며 런타임은 Git에 포함하지 않습니다.

```sh
python production/setup_runtime.py

# 수정한 침대 장면 한 프레임 미리보기
LUMINEX_PYTHON="$(command -v python)" LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
blender -b -t 1 --factory-startup --python-exit-code 1 \
  --python production/scene.py -- --scene 4 --sample 48 --width 1280 --samples 4

# 10개의 3D 촬영본 + 도시 오프닝·엔딩 → 전체 15장면
python production/build.py
python production/verify_media.py
python production/verify_motion.py
```

취침 촬영본의 잔잔한 호흡은 약 3.9초의 47프레임 루프를 사용합니다. 기상 촬영본은 전체 동작을 렌더링합니다. 대부분의 원본은 Cycles 4샘플과 안내 정보를 사용하는 디노이징으로 제작했고, 야외 인물과 가족 장면은 6샘플을 사용했습니다. 6·7번 장면은 같은 창문 터치 촬영본, 4·10번은 취침 촬영본, 11·12번은 자동 개폐 촬영본을 다른 화면·시간·설명으로 편집합니다. 11개의 장면 구간에 움직이는 인물이 등장합니다. 장면 사이에는 4프레임 디졸브를 적용하며 총 길이와 10초 경계를 유지합니다.

`assets/soundtrack.m4a`에는 승인된 한국어 내레이션(M3), 별도 창문 안내(F1), 잔잔한 피아노 음악이 들어 있습니다. 이번 시각 수정에서는 이 음성·음악을 재인코딩 없이 유지했습니다. 제품 이름은 LUMINEX(루미넥스)입니다.

`storyboard.json`은 장면 구성, `speech_segments.json`은 음성별 자막 타이밍입니다. 원본 모델·동작·재질은 `assets/`에, 출처와 조건은 `ATTRIBUTION.md`와 `licenses/`에 있습니다. 전체 출력은 `output/LUMINEX_Pohang_2035.mp4`와 `output/AI_Smart_Window_Pohang.mp4`에 동일하게 저장합니다. `verify_media.py`는 실제 MP4 헤더, 길이·프레임 수와 두 파일의 체크섬을 검사하고 본편 전체를 디코딩합니다. 동작 검사에는 렌더링할 때 생성하는 `camera_XX.json`이 필요합니다.
