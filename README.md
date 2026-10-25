# LUMINEX — 포항의 내일을 여는 창

2035년 포항을 배경으로 한 인공지능 스마트 윈도우 영상입니다. 15장면, 총 2분 30초입니다.

[전체 영상 다운로드](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/LUMINEX_Pohang_2035.mp4) · [30초 동작 미리보기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/motion_preview.mp4) · [음성 미리듣기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/audio_preview.mp3)

피부·머리카락·의상 텍스처가 있는 Rocketbox 캐릭터와 실제 관절 동작을 적용했습니다. 학생의 걷기와 창문 터치, 침대에서 일어나기, 휴대폰 조작, 아이의 블록 쌓기를 애니메이션으로 표현합니다. 가구는 Wayfair의 3D 모델로 교체하고 포항 해안 전망, 목재 바닥, 직물과 실내 조명을 새로 구성했습니다.

제품 로고와 창문 UI, 소개·엔딩 음성의 이름을 **LUMINEX(루미넥스)**로 통일했습니다. 한국어 내레이션, 별도 창문 안내 목소리와 잔잔한 피아노 음악을 함께 담았습니다. 장면은 10초 간격으로 전환하며 빠른 디졸브를 사용합니다.

![실제 LUMINEX MP4에서 추출한 장면](output/preview.jpg)

| 항목 | 검증 결과 |
| --- | --- |
| 실제 MP4 | `output/LUMINEX_Pohang_2035.mp4` |
| 길이 | 150초 · 15장면 |
| 영상 | H.264 · 1920×1080 · 24fps · 3,600프레임 |
| 음성·음악 | AAC 스테레오 · 44,100Hz |
| 인물 움직임 | 13개의 인물 장면에서 3D 관절 위치 변화 확인 |
| 파일 크기 | 53,057,970바이트 · 약 50.60MiB |
| 파일 무결성 | 본편 전체 디코딩 및 미리보기 재생 검사 통과 |

`output/AI_Smart_Window_Pohang.mp4`에도 동일한 완성본을 저장했습니다. 두 MP4 파일의 SHA-256은 같습니다. 저장소를 내려받아 `output/영상보기.html`을 열어 재생할 수도 있습니다.

[미디어 검증](output/verification.json) · [관절 움직임 검증](output/motion_verification.json) · [음성 검증](output/audio_verification.json) · [제작 원본과 실행 방법](production/README.md) · [자산 출처·라이선스](production/ATTRIBUTION.md)
