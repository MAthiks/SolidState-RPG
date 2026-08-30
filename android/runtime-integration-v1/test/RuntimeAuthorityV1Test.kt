import io.solidstate.android.runtime.RuntimeAuthorityV1
import io.solidstate.android.runtime.RuntimeEvidenceV1

private fun valid() = RuntimeEvidenceV1(
    checkpoint = RuntimeAuthorityV1.AUTHORITY_CHECKPOINT,
    checkpointId = RuntimeAuthorityV1.AUTHORITY_ID,
    checkpointRecordBlobSha1 = RuntimeAuthorityV1.AUTHORITY_RECORD_BLOB_SHA1,
    baseRuntimeZipSha256 = RuntimeAuthorityV1.BASE_RUNTIME_ZIP_SHA256,
    packageManifestSha256 = RuntimeAuthorityV1.PACKAGE_MANIFEST_SHA256,
    reconstructedThrough332 = true,
    sourcePackReady = true,
    privateSourcesEmbedded = false,
    multiplayerStatePartitioned = true,
    atomicSaveResume = true,
    actorBoundStrictReplay = true,
)

private fun expect(code: String, evidence: RuntimeEvidenceV1) {
    val result = RuntimeAuthorityV1.validate(evidence)
    check(result.code == code) { "Expected $code, got ${result.code}" }
    check(result.allowed == code.startsWith("ALLOW_")) { "allowed mismatch for $code" }
}

fun main() {
    var count = 0
    fun t(code: String, e: RuntimeEvidenceV1) { expect(code, e); count++ }

    t("ALLOW_CHECKPOINT_333_RUNTIME_ATTACH", valid())
    t("BLOCK_AUTHORITY_DOWNGRADE", valid().copy(checkpoint = 332))
    t("BLOCK_UNVERIFIED_FUTURE_AUTHORITY", valid().copy(checkpoint = 334))
    t("BLOCK_AUTHORITY_ID_MISMATCH", valid().copy(checkpointId = "OTHER"))
    t("BLOCK_AUTHORITY_RECORD_MISMATCH", valid().copy(checkpointRecordBlobSha1 = "0".repeat(40)))
    t("BLOCK_RUNTIME_PACKAGE_MISMATCH", valid().copy(baseRuntimeZipSha256 = "0".repeat(64)))
    t("BLOCK_PACKAGE_MANIFEST_MISMATCH", valid().copy(packageManifestSha256 = "0".repeat(64)))
    t("BLOCK_RUNTIME_CHAIN_INCOMPLETE", valid().copy(reconstructedThrough332 = false))
    t("BLOCK_PRIVATE_SOURCE_EMBEDDED", valid().copy(privateSourcesEmbedded = true))
    t("BLOCK_SOURCE_PACK_NOT_READY", valid().copy(sourcePackReady = false))
    t("BLOCK_PLAYER_PARTITION_UNVERIFIED", valid().copy(multiplayerStatePartitioned = false))
    t("BLOCK_SAVE_RESUME_UNVERIFIED", valid().copy(atomicSaveResume = false))
    t("BLOCK_STRICT_REPLAY_UNVERIFIED", valid().copy(actorBoundStrictReplay = false))

    println("RuntimeAuthorityV1: $count/$count PASS")
}
