"""Read a SQL artifact from a previously completed OpenAI Agents API turn."""

MAX_BYTES = 4096


class CodexArtifact:
    mode = 'codex-artifact'

    def __init__(self, client, session_id, turn_id):
        self.client = client
        self.session_id = session_id
        self.turn_id = turn_id

    def write(self):
        artifacts = self.client.beta.agents.sessions.artifacts
        for artifact in artifacts.list(self.session_id):
            if artifact.turn_id != self.turn_id or artifact.path != '/workspace/outputs/report.sql':
                continue
            with artifacts.with_streaming_response.content(
                artifact.id, session_id=self.session_id
            ) as response:
                content = bytearray()
                for chunk in response.iter_bytes(chunk_size=MAX_BYTES):
                    if len(content) + len(chunk) > MAX_BYTES:
                        raise ValueError('oversized artifact')
                    content.extend(chunk)
                return content.decode('utf-8')
        raise ValueError('artifact unavailable')
