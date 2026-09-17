# python-ffmpeg-audio-io

## プロジェクト概要
FFmpeg / FFprobe を Python 標準の `subprocess` で直接ラップし、オーディオファイルのメタデータ取得、デコード、および各種フォーマット（MP3, AAC, AIFF, Opus, FLAC）へのエンコードを行うための軽量かつ堅牢なオーディオ I/O ライブラリです。

## 設計方針・要件
1. **外部パッケージの制限**:
   - 音声処理の核としてサードパーティの重いラッパーライブラリ（`ffmpeg-python`, `pydub` 等）は使用せず、標準ライブラリ（`subprocess` 等）で直接 FFmpeg / FFprobe と通信を行う。
   - 生データ・数値配列の扱いには `numpy` を活用する。
2. **パッケージ・環境管理**:
   - 依存関係の管理、仮想環境の構築、テストの実行には `uv` を使用すること。
   - 使用するPythonのバージョンは **Python 3.14**（3.13以上対応）を使用すること。
3. **統一されたインターフェース**:
   - **デコード**: 入力ファイルの種類（MP3, WAV, AIFF, FLAC, AAC 等）によらず、統一された API（`decode()` 関数）により raw PCM データを保持する `PCM` オブジェクトへ変換する。
   - **メタデータ取得**: `get_audio_info()` を通じてサンプルレート、チャンネル数、ビットレート、再生時間などの音声メタデータを取得できる。
   - **エンコード**: 各フォーマット用のエンコーダークラス（`MP3Encoder`, `AACEncoder`, `AIFFEncoder`, `OpusEncoder`, `FLACEncoder`）は `BaseAudioEncoder` を継承し、統一された呼び出し形式 `__call__(pcm, output_path, overwrite=False)` を提供する。
4. **オーディオファイルのストリームとしての扱い**:
   - **一時ファイルの回避とパイプ活用**: ディスクへの一時ファイル生成に依存せず、FFmpeg プロセスの標準入出力パイプ（`pipe:0`, `pipe:1`）を活用して生 PCM データをバイナリストリームとして逐次処理する。
   - **読み込みストリーム**: 音声ファイルから生 PCM チャンクを逐次読み出す単一のリーダー（`AudioStreamReader`）を提供する（`with` 構文対応）。
   - **書き込みストリーム**:
     - 生 PCM チャンクを FFmpeg の標準入力（`pipe:0`）に逐次供給し、フォーマット変換を行う。
     - **出力先はファイルパスのみに限定する**: エンコード結果を直接ディスク上のファイルへ書き出させることで、OS パイプバッファ溢れ（約 64KB）に伴うデッドロック（相互待ちによるハングアップ）リスクを排除し、シンプルかつ堅牢な実装とする（`BytesIO` などのメモリ上ストリーム出力は対象外とする）。
     - 基底クラス（`BaseAudioStreamWriter`）を継承し、フォーマットごとのライタークラス（`MP3StreamWriter`, `AACStreamWriter` 等）を提供する（`with` 構文対応）。

## エラーハンドリング方針
1. **例外の定義**:
   - 基底: `PyFFmpegAudioIOError`（FFmpeg の標準エラー出力 `stderr` を保持可能）
   - 派生:
     - `FileReadError`: ファイルが存在しない、読み取り権限がない、または通常ファイルでない場合
     - `FileWriteError`: 出力先ファイルが既に存在し上書き不許可の場合、または書き込み権限がない場合
     - `FFmpegError`: FFmpeg または FFprobe のサブプロセス実行がエラーで終了した場合
     - `FFmpegNotFoundError`: FFmpeg または FFprobe の実行可能ファイルがシステム PATH に見つからない場合
     - `PCMFormatError`: 未対応または不正な PCM フォーマット、NumPy 変換非対応フォーマット（24-bit PCM 等）の場合
     - `StreamError`: ストリーム処理に関する基底例外
       - `StreamClosedError`: クローズ済みまたは終了済みのストリームに対して読み込み・書き込み等の I/O 操作を行った場合
       - `StreamBrokenError`: FFmpeg プロセスの予期せぬ終了、パイプ切断（BrokenPipeError）、またはストリーム途絶が発生した場合
2. **FFmpeg例外のラップ**:
   - 外部プロセス（`subprocess` による `ffmpeg` や `ffprobe` の実行）を伴う処理では、必ず実行失敗時（`FileNotFoundError`/`OSError` や `CalledProcessError` など）を想定した堅牢な例外処理を実装する。
   - エラー発生時は、FFmpeg が出力した標準エラー出力（stderr）のメッセージをキャッチし、分かりやすい Python の例外メッセージおよび例外オブジェクトの属性に含めて送出する。
3. **入力検証と型安全性**:
   - 存在しないファイルパスが指定された場合や、サポート対象外の拡張子・パラメータの場合は、適切な例外を早期に発生させる。
   - 外部入力や公開 API の境界では、適切な型や値の妥当性検証（`isinstance` チェック、Enum 検証、アライメントチェックなど）を行い、不正な入力に対しては早期に適切な例外（`TypeError` や `ValueError` など）を発生させる。

## 開発・品質管理
- **静的型チェック**: Pyright を使用する（`uv run pyright`）。PEP 561（`py.typed`）に準拠し、型ヒントを厳格に活用する。
- **Docstring**: パブリック API をはじめとするモジュール・クラス・関数・メソッドには必ず適切な docstring（Google スタイル準拠の Args, Returns, Raises 等）を付与する。
- **リンター・フォーマッター**: `uv run ruff check` / `uv run ruff format`
- **テスト**: `uv run pytest`
