// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SSServiceRecord.h"

/** How a load went. Anything but Loaded leaves OutRecord default-constructed. */
enum class ESSRecordLoad : uint8
{
	Loaded,
	/** No record for this player yet. */
	NotFound,
	/** The file exists but cannot be read or parsed, or its version is below 1. */
	Unreadable,
	/** Written by a newer build. Never overwrite it: the player would lose progress. */
	FromNewerVersion,
};

/**
 * Where service records live (TDD §6.3, ADR-032). Gameplay code never touches
 * files or SaveGame directly; it goes through this interface, so the dev-only
 * local provider can be replaced by a server-authoritative one without
 * touching gameplay.
 */
class SSPROG_API ISSPersistenceProvider
{
public:
	virtual ~ISSPersistenceProvider() = default;

	/** Load and migrate the record for PlayerId. OutError says why on anything but Loaded. */
	virtual ESSRecordLoad LoadServiceRecord(const FString& PlayerId, FSSServiceRecord& OutRecord, FString& OutError) = 0;

	virtual bool SaveServiceRecord(const FSSServiceRecord& Record, FString& OutError) = 0;

	/**
	 * Whether this provider's records can be trusted as proof of progress. A
	 * local provider is always false: its owner can edit the file, so nothing
	 * it holds may unlock anything another player can see.
	 */
	virtual bool IsAuthoritative() const = 0;
};

/**
 * DEV ONLY. One human-readable JSON file per player in a directory. Writes go
 * to a temporary file that is then moved over the record, so a crash mid-save
 * leaves the previous record intact. Not authoritative (TDD §6.3 point 4).
 */
class SSPROG_API FSSLocalDevPersistence : public ISSPersistenceProvider
{
public:
	explicit FSSLocalDevPersistence(const FString& InDirectory);

	virtual ESSRecordLoad LoadServiceRecord(const FString& PlayerId, FSSServiceRecord& OutRecord, FString& OutError) override;
	virtual bool SaveServiceRecord(const FSSServiceRecord& Record, FString& OutError) override;
	virtual bool IsAuthoritative() const override { return false; }

	/** Rename an unreadable record aside (".corrupt-<utc>.json") so a fresh one can be written. Returns the new path, or empty. */
	FString QuarantineRecord(const FString& PlayerId);

	/** Full path of PlayerId's record; empty for an unusable id. */
	FString PathFor(const FString& PlayerId) const;

	const FString& GetDirectory() const { return Directory; }

private:
	FString Directory;
};
