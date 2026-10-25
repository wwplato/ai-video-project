# LUMINEX — 포항의 내일을 여는 창

2035년 포항을 배경으로 한 인공지능 스마트 윈도우 영상입니다. 15장면, 총 2분 30초입니다.

[전체 영상 다운로드](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/LUMINEX_Pohang_2035.mp4) · [30초 동작 미리보기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/motion_preview.mp4) · [음성 미리듣기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/audio_preview.mp3)

인물의 걷기는 실제 위치 이동과 발 접촉에 맞추고, 멈추면 걷기 동작도 멈추도록 수정했습니다. 침대에서는 다리 위치를 유지하며 상체가 일어나고, 몸의 높이에 여유 공간을 더한 이불 표면을 적용했습니다. 피부·의상의 노멀맵, Cycles 조명과 안내 정보를 이용한 디노이징으로 재질과 그림자를 개선했습니다.

반투명 유리는 바깥 풍경의 색과 빛을 남기며 부드럽게 흐려집니다. 창문에는 투명한 화면이 나타나고, 터치하면 주간 예보로 전환되며 그래프가 움직입니다. 창문이 열릴 때는 유리·네 방향 프레임·손잡이가 함께 이동합니다. 원격 제어 장면의 학생은 야외 캠퍼스에 있으며, 집 안 창문의 움직임은 별도의 LIVE 화면에 표시합니다.

제품 로고와 창문 UI, 소개·엔딩 음성의 이름을 **LUMINEX(루미넥스)**로 통일했습니다. 한국어 내레이션, 별도 창문 안내 목소리와 잔잔한 피아노 음악을 함께 담았습니다. 장면은 10초 간격으로 전환하며 빠른 디졸브를 사용합니다.

![실제 LUMINEX MP4에서 추출한 장면](output/preview.jpg)

| 항목 | 검증 결과 |
| --- | --- |
| 실제 MP4 | `output/LUMINEX_Pohang_2035.mp4` |
| 길이 | 150초 · 15장면 |
| 영상 | H.264 · 1920×1080 · 24fps · 3,600프레임 |
| 음성·음악 | AAC 스테레오 · 44,100Hz |
| 인물 움직임 | 11개의 인물 장면에서 3D 관절 위치 변화 확인 |
| 파일 크기 | 29,548,870바이트 · 약 28.18MiB |
| 파일 무결성 | 본편 전체 디코딩 및 미리보기 재생 검사 통과 |

`output/AI_Smart_Window_Pohang.mp4`에도 동일한 완성본을 저장했습니다. 두 MP4 파일의 SHA-256은 같습니다. 저장소를 내려받아 `output/영상보기.html`을 열어 재생할 수도 있습니다.

[미디어 검증](output/verification.json) · [관절 움직임 검증](output/motion_verification.json) · [음성 검증](output/audio_verification.json) · [제작 원본과 실행 방법](production/README.md) · [자산 출처·라이선스](production/ATTRIBUTION.md)
