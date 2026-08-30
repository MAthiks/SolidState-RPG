package io.solidstate.android.runtime

data class RuntimeEvidenceV1(
    val checkpoint: Int,
    val checkpointId: String,
    val checkpointRecordBlobSha1: String,
    val baseRuntimeZipSha256: String,
    val packageManifestSha256: String,
    val reconstructedThrough332: Boolean,
    val sourcePackReady: Boolean,
    val privateSourcesEmbedded: Boolean,
    val multiplayerStatePartitioned: Boolean,
    val atomicSaveResume: Boolean,
    val actorBoundStrictReplay: Boolean,
)

data class RuntimeGateResultV1(
    val allowed: Boolean,
    val code: String,
)

object RuntimeAuthorityV1 {
    const val AUTHORITY_CHECKPOINT = 333
    const val AUTHORITY_ID = "MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2"
    const val AUTHORITY_RECORD_BLOB_SHA1 = "965695bdc3ebe13f7337bb491796f6a193bd8fa6"
    const val BASE_RUNTIME_ZIP_SHA256 = "75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add"
    const val PACKAGE_MANIFEST_SHA256 = "aba613f506e92248ee7e8ffd4a190c0d293b9e638be116659ad06a4e9a703dc9"

    fun validate(evidence: RuntimeEvidenceV1): RuntimeGateResultV1 {
        if (evidence.checkpoint < AUTHORITY_CHECKPOINT) {
            return block("BLOCK_AUTHORITY_DOWNGRADE")
        }
        // This contract is pinned to the exact certified authority. A future checkpoint
        // must update this Android contract rather than being accepted by number alone.
        if (evidence.checkpoint != AUTHORITY_CHECKPOINT) {
            return block("BLOCK_UNVERIFIED_FUTURE_AUTHORITY")
        }
        if (evidence.checkpointId != AUTHORITY_ID) {
            return block("BLOCK_AUTHORITY_ID_MISMATCH")
        }
        if (!secureEquals(evidence.checkpointRecordBlobSha1, AUTHORITY_RECORD_BLOB_SHA1)) {
            return block("BLOCK_AUTHORITY_RECORD_MISMATCH")
        }
        if (!secureEquals(evidence.baseRuntimeZipSha256, BASE_RUNTIME_ZIP_SHA256)) {
            return block("BLOCK_RUNTIME_PACKAGE_MISMATCH")
        }
        if (!secureEquals(evidence.packageManifestSha256, PACKAGE_MANIFEST_SHA256)) {
            return block("BLOCK_PACKAGE_MANIFEST_MISMATCH")
        }
        if (!evidence.reconstructedThrough332) {
            return block("BLOCK_RUNTIME_CHAIN_INCOMPLETE")
        }
        if (evidence.privateSourcesEmbedded) {
            return block("BLOCK_PRIVATE_SOURCE_EMBEDDED")
        }
        if (!evidence.sourcePackReady) {
            return block("BLOCK_SOURCE_PACK_NOT_READY")
        }
        if (!evidence.multiplayerStatePartitioned) {
            return block("BLOCK_PLAYER_PARTITION_UNVERIFIED")
        }
        if (!evidence.atomicSaveResume) {
            return block("BLOCK_SAVE_RESUME_UNVERIFIED")
        }
        if (!evidence.actorBoundStrictReplay) {
            return block("BLOCK_STRICT_REPLAY_UNVERIFIED")
        }
        return RuntimeGateResultV1(true, "ALLOW_CHECKPOINT_333_RUNTIME_ATTACH")
    }

    private fun block(code: String) = RuntimeGateResultV1(false, code)

    private fun secureEquals(left: String, right: String): Boolean {
        if (left.length != right.length) return false
        var diff = 0
        for (i in left.indices) {
            diff = diff or (left[i].code xor right[i].code)
        }
        return diff == 0
    }
}
