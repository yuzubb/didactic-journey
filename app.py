from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
from pathlib import Path

app = Flask(__name__)

# プロキシ設定（環境変数から取得）
PROXY = os.environ.get('PROXY_URL', '')  # 例: 'http://user:pass@proxy.example.com:8080'

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'endpoints': {
            '/info': 'GET - 動画情報取得 (params: url)',
            '/download': 'GET - 動画ダウンロード (params: url, format)',
            '/formats': 'GET - 利用可能なフォーマット一覧 (params: url)'
        }
    })

@app.route('/info', methods=['GET'])
def get_info():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    if PROXY:
        ydl_opts['proxy'] = PROXY
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'thumbnail': info.get('thumbnail'),
                'description': info.get('description'),
                'view_count': info.get('view_count'),
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/formats', methods=['GET'])
def get_formats():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    if PROXY:
        ydl_opts['proxy'] = PROXY
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []):
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': f.get('ext'),
                    'resolution': f.get('resolution'),
                    'filesize': f.get('filesize'),
                    'format_note': f.get('format_note'),
                })
            return jsonify({'formats': formats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    format_id = request.args.get('format', 'best')
    
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    if PROXY:
        ydl_opts['proxy'] = PROXY
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=os.path.basename(filename)
                )
            else:
                return jsonify({'error': 'Download failed'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
