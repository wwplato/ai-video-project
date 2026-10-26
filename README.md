# LUMINEX — 포항의 내일을 여는 창

2035년 포항을 배경으로 한 인공지능 스마트 윈도우 영상입니다. 15장면, 총 2분 30초입니다.

[전체 영상 다운로드](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/LUMINEX_Pohang_2035.mp4) · [30초 동작 미리보기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/motion_preview.mp4) · [음성 미리듣기](https://github.com/wwplato/ai-video-project/raw/refs/heads/main/output/audio_preview.mp3)

창문을 샴페인색 금속 프레임·복층 유리 가장자리·고무 실링·매립형 손잡이·센서와 잠금 볼트로 다시 구성했습니다. 손잡이 확대에서 창문 전체로 이어지는 제품 컷을 넣고, 개폐 장면은 네 방향 프레임이 자막 위에 보이도록 촬영했습니다. 오른쪽 벽·창문 주변 벽·천장과 간접조명을 구성하고, 야간에는 넓은 구도와 별도 벽 조명으로 창문 양옆 벽이 계속 보이도록 했습니다.

한쪽 발만 계속 앞서던 보행을 고쳐 좌우 발이 번갈아 앞으로 나가도록 했습니다. 골반의 좌우 높이를 맞추고 위아래 출렁임과 착지 때의 튐을 줄였습니다. 보행 구간은 원본 24fps이며, 학생은 약 1.24m를 네 걸음으로 이동한 뒤 멈춥니다. 침대의 몸과 이불 간격 보정도 유지했습니다.

비는 창밖의 빗줄기와 유리를 흐르는 렌즈 모양 물방울로 나눴습니다. 실제 유리 좌표와 가림 마스크를 사용해 물방울이 창문과 함께 움직이고, 벽·가구·사람에는 비가 덧씌워지지 않도록 합니다. 태풍은 별도 해안 배경을 사용해 먹구름·폭우·거친 파도와 흰 포말이 나타납니다.

반투명 모드는 풍경의 색과 빛을 유지합니다. 투명한 창문 화면에서는 예보와 그래프가 움직이고, 원격 제어 장면은 포항 환호공원 스페이스워크 콘셉트 배경과 집 안 창문의 LIVE 화면을 함께 보여줍니다.

제품 로고와 창문 UI, 소개·엔딩 음성의 이름을 **LUMINEX(루미넥스)**로 통일했습니다. 한국어 내레이션, 별도 창문 안내 목소리와 잔잔한 피아노 음악을 함께 담았습니다. 장면은 10초 간격으로 전환하며 빠른 디졸브를 사용합니다.

![실제 LUMINEX MP4에서 추출한 장면](output/preview.jpg)

| 항목 | 검증 결과 |
| --- | --- |
| 실제 MP4 | `output/LUMINEX_Pohang_2035.mp4` |
| 길이 | 150초 · 15장면 |
| 영상 | H.264 · 1920×1080 · 24fps · 3,600프레임 |
| 음성·음악 | AAC 스테레오 · 44,100Hz |
| 인물 움직임 | 10개의 인물 장면에서 3D 관절 위치 변화 확인 |
| 파일 크기 | 32,598,311바이트 · 약 31.09MiB |
| 파일 무결성 | 본편 전체 디코딩 및 미리보기 재생 검사 통과 |

`output/AI_Smart_Window_Pohang.mp4`에도 동일한 완성본을 저장했습니다. 두 MP4 파일의 SHA-256은 같습니다. 저장소를 내려받아 `output/영상보기.html`을 열어 재생할 수도 있습니다.

[미디어 검증](output/verification.json) · [관절 움직임 검증](output/motion_verification.json) · [음성 검증](output/audio_verification.json) · [제작 원본과 실행 방법](production/README.md) · [자산 출처·라이선스](production/ATTRIBUTION.md)
