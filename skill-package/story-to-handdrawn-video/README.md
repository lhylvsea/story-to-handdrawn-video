# story-to-handdrawn-video

将中文故事、文章审阅后的文案、有序图片或用户提供的角色原型转换为 3:4 竖屏手绘动画，并支持可复核的配音后期。

本 Skill 的仓库是 [lhylvsea/any-to-handdrawn-video](https://github.com/lhylvsea/any-to-handdrawn-video)。Skill 名称暂时保留 `story-to-handdrawn-video`，用于兼容已有调用方式。

## 安装

```bash
npx skills add lhylvsea/any-to-handdrawn-video --skill story-to-handdrawn-video
```

## 你可以直接这样说

- “把这段故事做成彩铅日记漫画，先给我分镜和预览。”
- “用我上传的角色原型做固定 IP，制作一版手绘视频。”
- “以海洋哥 IP 做成配音版成片，默认不要底部字幕，语速约 1.2 倍。”
- “文章内容先输出原文与视频文案 diff，确认后再生成画面和配音。”

## 默认输出

基础渲染先输出静音画面轨 `out/picture_silent.mp4`。用户要求“配音版成片”时，再运行：

```bash
python3 scripts/postprocess_voiceover.py \
  --storyboard storyboard.json \
  --video out/picture_silent.mp4 \
  --output out/picture_voiceover.mp4
```

配音后期默认：

- 视频和旁白同步加速约 `1.2x`，默认输出约为原时长的 5/6；
- MP4 只映射视频和音频，不携带字幕流或底部字幕；
- 默认不生成 `.srt`/`.vtt`；明确要求外挂字幕时才追加 `--subtitle-mode srt`；
- 旁白另存为 `.m4a`，运行参数和镜头时长写入 JSON manifest；
- 保留逐镜头音频片段，方便用户后续调整。

画面内的手绘标题、关键词和镜头文字属于画面设计，不等同于底部旁白字幕。

## 前置条件

- [ ] Node.js/npm 与项目依赖
- [ ] Python 3
- [ ] FFmpeg 与 FFprobe
- [ ] `edge-tts` 命令（需要在线 TTS 时）
- [ ] Codex Image2 生成能力，或用户明确选择并配置的 API fallback

用户原型图只作为角色身份参考，不会自动复制进公开仓库。文章内容必须先经过审阅确认；没有授权的第三方图片只作构图参考，不直接发布。

## 验证

```bash
python3 scripts/validate_skill.py skill-package/story-to-handdrawn-video
python3 scripts/trigger_eval.py skill-package/story-to-handdrawn-video \
  --cases skill-package/story-to-handdrawn-video/evals/trigger_cases.json \
  --output skill-package/story-to-handdrawn-video/reports/trigger-eval.json
python3 scripts/export_skill_ir.py skill-package/story-to-handdrawn-video \
  --output skill-package/story-to-handdrawn-video/reports/skill-ir.json
npm run check:storyboard
```

配音版完成后，用 FFprobe 检查 `stream=subtitle` 为空，并确认视频与音频时长相同或仅有容器级帧舍入差异。

## Troubleshooting

| 问题 | 处理 |
| --- | --- |
| 找不到 `edge-tts` | 安装 Edge TTS CLI，或使用 `--edge-tts` 指定完整路径。 |
| 找不到 FFmpeg/FFprobe | 安装 FFmpeg，或使用 `--ffmpeg`、`--ffprobe` 指定路径。 |
| 文章文案未确认 | 先运行 `--mode review`，确认 diff 后再生成。 |
| 角色不一致 | 同时传入 `--character-profile` 和 `--character-reference`，不要只用文字描述。 |
| 仍然需要字幕 | 显式使用 `--subtitle-mode srt`；它生成外挂字幕，不会烧录进 MP4。 |

## License

MIT License. See [LICENSE](LICENSE).

Upstream inspiration: [gnipbao/story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video).
