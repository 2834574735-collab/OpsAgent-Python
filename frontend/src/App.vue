<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { marked } from 'marked'

interface RestartAction {
  action: 'restart'
  hostname: string
  token: string
  message?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  restart?: RestartAction
  restartLoading?: boolean
  restartDone?: boolean
}

const API_BASE = '/api/v1'

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const chatBox = ref<HTMLElement | null>(null)

function renderMarkdown(content: string): string {
  return marked.parse(content) as string
}

function extractRestart(content: string): { content: string; restart?: RestartAction } {
  const match = content.match(/\{[\s\S]*?"action"\s*:\s*"restart"[\s\S]*?\}/)
  if (!match) return { content }

  try {
    const data = JSON.parse(match[0]) as RestartAction
    if (data.action === 'restart' && data.token && data.hostname) {
      return { content: content.replace(match[0], '').trim(), restart: data }
    }
  } catch {
    // JSON 不完整时按普通文本展示
  }
  return { content }
}

function pushAssistant(content: string) {
  const { content: text, restart } = extractRestart(content)
  messages.value.push({ role: 'assistant', content: text || content, restart })
}

async function scrollToBottom() {
  await nextTick()
  if (chatBox.value) {
    chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: 'vue-test-1' }),
    })

    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(data?.detail || `请求失败（${response.status}）`)
    }

    pushAssistant(data.reply)
  } catch (error) {
    pushAssistant(`请求出错：${(error as Error).message}`)
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function confirmRestart(message: Message) {
  const action = message.restart
  if (!action || message.restartLoading || message.restartDone) return

  message.restartLoading = true
  try {
    const response = await fetch(`${API_BASE}/restart/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hostname: action.hostname, token: action.token }),
    })

    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(data?.detail || `确认失败（${response.status}）`)
    }

    message.restartDone = true
    pushAssistant(data.reply)
  } catch (error) {
    pushAssistant(`确认失败：${(error as Error).message}`)
  } finally {
    message.restartLoading = false
    await scrollToBottom()
  }
}
</script>

<template>
  <div class="chat-app">
    <header class="chat-header">OpsAgent 运维助手</header>

    <main ref="chatBox" class="chat-body">
      <p v-if="!messages.length" class="empty-tip">
        你好，我是 OpsAgent，可以帮你查询服务器状态、分析运维问题。
      </p>

      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message-row"
        :class="message.role"
      >
        <div class="bubble">
          <div
            v-if="message.role === 'assistant'"
            class="markdown"
            v-html="renderMarkdown(message.content)"
          ></div>
          <span v-else>{{ message.content }}</span>

          <button
            v-if="message.restart && !message.restartDone"
            class="restart-btn"
            :disabled="message.restartLoading"
            @click="confirmRestart(message)"
          >
            {{ message.restartLoading ? '正在重启…' : '确认重启' }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="message-row assistant">
        <div class="bubble typing">思考中…</div>
      </div>
    </main>

    <footer class="chat-input">
      <input
        v-model="inputText"
        type="text"
        placeholder="输入你的问题，按回车发送"
        @keyup.enter="sendMessage"
      />
      <button :disabled="loading || !inputText.trim()" @click="sendMessage">发送</button>
    </footer>
  </div>
</template>

<style>
html,
body,
#app {
  height: 100%;
}

#app {
  display: flex;
  max-width: none;
  margin: 0;
  padding: 0;
}

@media (min-width: 1024px) {
  body {
    display: block;
    place-items: unset;
  }

  #app {
    display: flex;
    grid-template-columns: none;
  }
}
</style>

<style scoped>
.chat-app {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fb;
}

.chat-header {
  flex: none;
  padding: 14px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e5e8ef;
  font-size: 17px;
  font-weight: 600;
  color: #1f2937;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-tip {
  text-align: center;
  color: #9aa4b2;
  font-size: 14px;
  margin-top: 40px;
}

.message-row {
  display: flex;
  margin-bottom: 14px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}

.user .bubble {
  background: #2563eb;
  color: #ffffff;
  border-bottom-right-radius: 2px;
  white-space: pre-wrap;
}

.assistant .bubble {
  background: #ffffff;
  color: #1f2937;
  border: 1px solid #e5e8ef;
  border-bottom-left-radius: 2px;
}

.typing {
  color: #9aa4b2;
}

.restart-btn {
  display: block;
  margin-top: 10px;
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  background: #dc2626;
  color: #ffffff;
  font-size: 13px;
  cursor: pointer;
}

.restart-btn:hover:not(:disabled) {
  background: #b91c1c;
}

.restart-btn:disabled {
  background: #f0a3a3;
  cursor: not-allowed;
}

.markdown :deep(p) {
  margin: 0 0 8px;
}

.markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
  font-size: 13px;
}

.markdown :deep(th),
.markdown :deep(td) {
  border: 1px solid #dfe3ea;
  padding: 6px 10px;
  text-align: left;
}

.markdown :deep(th) {
  background: #f2f5fa;
}

.markdown :deep(pre) {
  background: #f6f8fa;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown :deep(code) {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}

.chat-input {
  flex: none;
  display: flex;
  gap: 10px;
  padding: 14px 20px;
  background: #ffffff;
  border-top: 1px solid #e5e8ef;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d5dae3;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.chat-input input:focus {
  border-color: #2563eb;
}

.chat-input button {
  padding: 10px 22px;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
}

.chat-input button:disabled {
  background: #a9bce6;
  cursor: not-allowed;
}
</style>
