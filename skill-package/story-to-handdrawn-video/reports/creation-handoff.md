# Creation handoff — story-to-handdrawn-video v1.2.0

## 1. Result

- Skill：`story-to-handdrawn-video` v1.2.0
- Job：将中文故事、文章审阅后的文案、图片和角色 IP 转为手绘视频；用户要求配音版时，默认同步约 1.2 倍并交付不含字幕流的 MP4。
- 本地路径：`skill-package/story-to-handdrawn-video/`
- 发布状态：功能已写入目标仓库分支；GitHub PR/默认分支发布仍待本轮门禁完成。

## 2. Reference skills studied

- HyperFrames：学习独立媒体轨道、显式时间字段和字幕/TTS 分层；落到 `postprocess_voiceover.py` 的场景时间轴、音画同步和字幕 opt-in。
- video-use：学习 audio-first、输出时间轴和 FFprobe 终审；落到音频先编码、显式 `-map`、无字幕流检查和黑帧检查。
- 上游 story-to-handdrawn-video：学习静音 Remotion 基础轨与后期解耦；落到保留 `picture_silent.mp4`，新增独立配音后期，不破坏原有静音输出。

## 3. Absorbed and rejected

- 保留：静音基础轨、角色原型引用、文章内容审阅、独立旁白、FFprobe 验证。
- 适配：默认 `speed=1.2`；默认 `subtitle-mode=none`；需要字幕时只生成外挂 SRT，不烧录或 mux。
- 舍弃：默认底部字幕、默认 SRT/VTT、未审查远程候选代码和不相关的视频引擎迁移。
- 原创：单脚本完成逐镜头 TTS、精确填充、同步变速、音画合成、manifest 和可选字幕的后期流程。

## 4. Advantages and highlights

- **[design advantage]** 新增后期脚本只显式映射视频和音频轨道，因此输入容器里即使存在额外数据，也不会默认被带入成片。
- **[validated advantage]** 4/4 本地单元测试通过，覆盖 1.2 倍 `atempo`、FFmpeg 限制拆链、标点清理和默认契约。
- **[validated advantage]** 真实成片冒烟测试已检查 1080×1440、音画时长、字幕流为空、音频响度和黑帧：输出时长约 153.318 秒，视频/音频轨道存在且字幕流为 0，无黑帧，音频峰值约 -5.1 dB。
- **[hypothesis]** 1.2 倍同步变速预计比原始旁白更适合当前短视频脚本，但尚无第三方人工盲评证据，仍标记为 `missing evidence`。

## 5. Verification and limits

- 已通过：Python 编译、4/4 Skill 单元测试、Qiaomu `validate_skill`、13/13 触发评测、Skill IR、TypeScript 类型检查、真实配音后期冒烟。
- 待完成：目标 GitHub 仓库的分支/PR 门禁与人工审阅；发布后还需进行 clean install 复核。
- 已知基线问题：仓库现有 `npm run check:storyboard` 因未提交的历史生成图片资源失败；本次变更未修改这些 storyboard 或资源引用。
- 限制：配音依赖本地 `edge-tts`、FFmpeg、FFprobe；远程 TTS 的网络可用性、音色质量和跨平台安装仍需用户环境验证。
- 权限边界：不把用户上传的角色原型图、绝对路径、Token、Cookie 或本次个人成片写入公开仓库。
