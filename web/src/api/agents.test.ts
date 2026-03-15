import { describe, it, expect, vi } from "vitest"
import { getAgents, createAgentStatusWebSocket } from "./agents"
import type { Agent } from "../types"

// Mock the apiClient
vi.mock("./client", () => ({
  default: {
    get: vi.fn()
  }
}))

describe("agents API", () => {
  describe("getAgents", () => {
    it("should fetch agents from the API", async () => {
      const mockAgents: Agent[] = [
        { id: "1", name: "Plot Agent", status: "idle" },
        { id: "2", name: "Character Agent", status: "running" }
      ]

      const apiClient = await import("./client")
      vi.mocked(apiClient.default.get).mockResolvedValueOnce({ data: mockAgents })

      const result = await getAgents()

      expect(result).toEqual(mockAgents)
      expect(apiClient.default.get).toHaveBeenCalledWith("/agents")
    })
  })

  describe("createAgentStatusWebSocket", () => {
    it("should create a WebSocket connection", () => {
      const onMessage = vi.fn()
      const onOpen = vi.fn()
      const onError = vi.fn()

      const ws = createAgentStatusWebSocket("ws://localhost:8000/ws/agents", onMessage, onOpen, onError)

      expect(ws).toBeInstanceOf(WebSocket)
      expect(ws.url).toBe("ws://localhost:8000/ws/agents")
    })
  })
})
