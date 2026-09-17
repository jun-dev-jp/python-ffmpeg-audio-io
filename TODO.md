# TODO / Roadmap

## Phase 1: 基本フォーマットとデータ構造の補完（優先度: 高）
- [ ] **WAV (RIFF WAVE) サポート**
  - [ ] `WAVEncoder` の実装（`.wav` へのエンコード、16/24/32bit PCM等）
  - [ ] `WAVStreamWriter` の実装（WAV へのストリーミング書き込み）
  - [ ] テストの追加 (`tests/test_encoders.py`, `tests/test_stream_writer.py` 等)
  - [ ] `examples/wav_encoder.py` および README への記載
- [ ] **`PCM` クラスのユーティリティ拡充**
  - [ ] `num_frames` プロパティの追加（総フレーム数の取得）
  - [ ] `duration` プロパティの追加（音声の長さ[秒]の取得）
  - [ ] 単体テストの追加

## Phase 2: デコード機能の強化（優先度: 高〜中）
- [ ] **デコード時のリサンプリング & チャンネル変換**
  - [ ] `decode()` に `sample_rate` 引数を追加（任意レートへリサンプル）
  - [ ] `decode()` に `channels` 引数を追加（Mono/Stereo への変換）
  - [ ] `AudioStreamReader` への同様のオプション反映
- [ ] **区間指定デコード (シーク & 切り出し)**
  - [ ] `decode()` に `start_time`（開始秒）および `duration`（切り出し秒）オプションを追加
  - [ ] FFmpeg の `-ss` および `-t` 引数の安全な適用とテスト

## Phase 3: ハイレベル API & 利便性向上（優先度: 中）
- [ ] **汎用 `encode()` 関数の実装**
  - [ ] 出力ファイルパスの拡張子（`.mp3`, `.wav`, `.flac` 等）から適切なエンコーダを自動選択して実行する `encode(pcm, output_path, **kwargs)` の提供
  - [ ] ドキュメントおよびサンプルの追加
- [ ] **インメモリ / バイト列デコード (`decode_bytes`)**
  - [ ] `bytes` または `BinaryIO` からテンポラリファイルなしでデコードする関数の実装（FFmpeg の `pipe:0` 入力）

## Phase 4: メタデータ & 堅牢性向上（優先度: 低〜中）
- [ ] **エンコード時のメタデータ付与**
  - [ ] ID3タグやVORBISコメント（タイトル、アーティスト、アルバム名など）を設定できる引数の追加
- [ ] **サンプリングレート / チャンネルの柔軟化**
  - [ ] `PCMSampleRate` / `PCMChannels` に未定義の特殊な値が来ても許容できるよう、正の整数値をサポート
