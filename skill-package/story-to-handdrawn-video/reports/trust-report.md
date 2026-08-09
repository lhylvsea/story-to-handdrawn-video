# Trust boundary and rollback report

## Public package boundary

- 公开文件只包含渲染器源码、Skill 说明、测试和脱敏的验证资料。
- 用户文章正文、用户上传角色原型图、个人视频、绝对路径、Cookie、Token 和 API key 不得进入 Skill 包、评测或 README。
- `edge-tts`、FFmpeg 和 FFprobe 是运行时依赖；脚本只执行用户本机已安装并明确指定的工具。
- 文章 URL 的读取、远程 TTS 和图片服务属于用户授权范围；来源不可读或授权不明确时停止，不用标题猜正文。

## Output boundary

- 基础产物：静音 H.264 画面轨。
- 配音产物：显式映射的视频 + AAC 音频，默认 1.2 倍同步变速。
- 字幕默认关闭；`--subtitle-mode srt` 仅产生外挂文件，不烧录、不 mux。
- manifest 记录运行参数和场景时长，不记录密钥或用户原始私密内容。

## Rollback boundary

- 新后期功能位于 `scripts/postprocess_voiceover.py` 和 Skill 说明层，不改变既有 Remotion 场景组件与静音输出命令。
- 若配音后期失败，删除/忽略新生成的 `picture_voiceover*` 输出即可回退到 `picture_silent.mp4`。
- 发布使用功能分支和 PR；不直接写目标默认分支。

## Missing evidence

- 尚未完成公开仓库 PR 的人工 review、跨平台 clean install 和第三方人工音质评审。
