import os
import glob

base = r'C:\Users\migue\Videos\StoryVideos'

for ch_num in range(0, 25):
    ch_dir = os.path.join(base, f'Chapter{ch_num}')
    if not os.path.isdir(ch_dir):
        print(f'Ch{ch_num}: DIRECTORY MISSING')
        continue

    files = os.listdir(ch_dir)

    # Audio files
    audio = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.m4a', '.flac'))]
    # Lyrics
    lyrics = [f for f in files if 'lyrics' in f.lower() or 'lyric' in f.lower()]
    # Text
    text = [f for f in files if f.lower().endswith('.txt') and 'text' in f.lower()]
    # Prompts
    prompts = [f for f in files if 'prompt' in f.lower()]
    # Captions
    captions = [f for f in files if 'caption' in f.lower()]
    # Suno styles
    suno = [f for f in files if 'suno' in f.lower()]
    # Video clips (not final, not intro)
    clips = [f for f in files if f.lower().endswith('.mp4') and 'final' not in f.lower() and 'intro' not in f.lower()]
    # Final video
    final = [f for f in files if f.lower().endswith('.mp4') and 'final' in f.lower()]
    # Intro
    intro = [f for f in files if f.lower().endswith('.mp4') and 'intro' in f.lower()]

    print(f'Ch{ch_num:>2}: Audio={len(audio)} Lyrics={len(lyrics)} Text={len(text)} Prompts={len(prompts)} Captions={len(captions)} Suno={len(suno)} Clips={len(clips)} Final={len(final)} Intro={len(intro)}')
    if audio: print(f'       Audio: {audio}')
    if lyrics: print(f'       Lyrics: {lyrics}')
    if text: print(f'       Text: {text}')
    if prompts: print(f'       Prompts: {prompts}')
    if final: print(f'       Final: {final}')
