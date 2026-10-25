# LUMINEX · 3D 영상 원본

2035년 포항을 배경으로 한 15장면, 150초 영상입니다. Blender 4.3.2, FFmpeg, Python 3.12, Pillow, NumPy를 사용했습니다. 한국어 글꼴은 Noto Sans CJK입니다.

`scene.py`는 피부·의상 텍스처가 포함된 Rocketbox 캐릭터를 불러와, 인체 동작을 각 체형에 맞게 리타기팅합니다. 관절을 가진 메시가 실제로 변형되며 걷기, 기상, 창문 터치, 휴대폰 조작, 블록 이동을 표현합니다. 가구 GLB와 목재 재질, 조명, 창문을 3D 공간에 배치하고 Eevee로 렌더링합니다. 해안 풍경은 생성한 콘셉트 이미지입니다.

`assets/`의 Blender 파일에는 캐릭터 텍스처가 포함되어 있습니다. `motion.json.gz`는 원본 동작의 관절 회전을 샘플링한 데이터입니다. `ATTRIBUTION.md`와 `licenses/`에 원본 출처와 이용 조건을 보관합니다.

```sh
# 학생의 창문 터치: 10초, 1280×720, 초당 12개 3D 프레임
blender -b -t 1 --factory-startup --python production/scene.py -- --scene 5 --frames 120 --width 1280

# 9개의 3D 촬영본 → 13개의 인물 장면 + 도시 오프닝·엔딩
python production/build.py
```

전체 제작은 3D 원본을 12fps로 렌더링한 뒤 움직임을 보간해 24fps로 출력합니다. 최종 해상도는 1920×1080입니다. `composite.py`는 최종 크기에서 한국어 자막·LUMINEX 로고를 그리고, 3D 창문 위치를 추적하여 UI를 투시 변환합니다. 6번과 7번 장면의 창문 터치, 4번과 10번 장면의 취침 동작, 8·11·12번 장면의 창문 주변 동작은 촬영본을 공유하고 화면·날씨·음성·설명을 달리 편집했습니다.

장면 사이에는 4프레임의 빠른 디졸브를 사용하며 각 장면의 10초 경계를 유지합니다. `assets/soundtrack.m4a`에는 자연스러운 한국어 내레이션(M3), 별도 창문 안내(F1), 잔잔한 피아노 음악이 함께 들어 있습니다. 이번 변경에서는 제품 소개와 엔딩 음성에 루미넥스 이름을 반영했습니다.

`storyboard.json`은 장면 구성, `speech_segments.json`은 음성별 자막 타이밍입니다. 전체 출력은 `output/AI_Smart_Window_Pohang.mp4`에 저장됩니다.
