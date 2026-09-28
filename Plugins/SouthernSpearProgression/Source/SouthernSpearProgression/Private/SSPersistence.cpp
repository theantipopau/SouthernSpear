// Copyright Southern Spear. All Rights Reserved.

#include "SSPersistence.h"

#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "JsonObjectConverter.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "SSProgressionRules.h"

FSSLocalDevPersistence::FSSLocalDevPersistence(const FString& InDirectory)
	: Directory(InDirectory)
{
}

FString FSSLocalDevPersistence::PathFor(const FString& PlayerId) const
{
	const FString Safe = FSSProgressionRules::SanitisePlayerId(PlayerId);
	return Safe.IsEmpty() ? FString() : FPaths::Combine(Directory, FString::Printf(TEXT("ServiceRecord_%s.json"), *Safe));
}

ESSRecordLoad FSSLocalDevPersistence::LoadServiceRecord(const FString& PlayerId, FSSServiceRecord& OutRecord, FString& OutError)
{
	OutRecord = FSSServiceRecord();
	const FString Path = PathFor(PlayerId);
	if (Path.IsEmpty())
	{
		OutError = FString::Printf(TEXT("Player id '%s' has no usable characters."), *PlayerId);
		return ESSRecordLoad::Unreadable;
	}
	if (!IFileManager::Get().FileExists(*Path))
	{
		OutError = FString::Printf(TEXT("No service record at %s."), *Path);
		return ESSRecordLoad::NotFound;
	}

	FString Json;
	if (!FFileHelper::LoadFileToString(Json, *Path))
	{
		OutError = FString::Printf(TEXT("Could not read %s."), *Path);
		return ESSRecordLoad::Unreadable;
	}
	TSharedPtr<FJsonObject> Object;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
	if (!FJsonSerializer::Deserialize(Reader, Object) || !Object.IsValid())
	{
		OutError = FString::Printf(TEXT("%s is not valid JSON."), *Path);
		return ESSRecordLoad::Unreadable;
	}

	// Check the version before importing anything: a newer record may have
	// fields this build would silently drop on the next save.
	int32 Version = 0;
	if (!Object->TryGetNumberField(TEXT("schemaVersion"), Version))
	{
		OutError = FString::Printf(TEXT("%s has no schemaVersion."), *Path);
		return ESSRecordLoad::Unreadable;
	}
	if (Version > FSSServiceRecord::CurrentSchemaVersion)
	{
		OutError = FString::Printf(TEXT("%s is schema version %d; this build reads up to %d. It was left untouched."),
			*Path, Version, FSSServiceRecord::CurrentSchemaVersion);
		return ESSRecordLoad::FromNewerVersion;
	}

	FSSServiceRecord Loaded;
	if (!FJsonObjectConverter::JsonObjectToUStruct(Object.ToSharedRef(), &Loaded, 0, 0))
	{
		OutError = FString::Printf(TEXT("%s does not match the service record layout."), *Path);
		return ESSRecordLoad::Unreadable;
	}
	FString MigrateError;
	if (!FSSProgressionRules::Migrate(Loaded, MigrateError))
	{
		OutError = FString::Printf(TEXT("%s: %s"), *Path, *MigrateError);
		return ESSRecordLoad::Unreadable;
	}
	OutRecord = MoveTemp(Loaded);
	return ESSRecordLoad::Loaded;
}

bool FSSLocalDevPersistence::SaveServiceRecord(const FSSServiceRecord& Record, FString& OutError)
{
	const FString Path = PathFor(Record.PlayerId);
	if (Path.IsEmpty())
	{
		OutError = FString::Printf(TEXT("Player id '%s' has no usable characters."), *Record.PlayerId);
		return false;
	}
	FString Json;
	if (!FJsonObjectConverter::UStructToJsonObjectString(Record, Json))
	{
		OutError = TEXT("Could not serialise the service record.");
		return false;
	}
	IFileManager::Get().MakeDirectory(*Directory, /*Tree=*/ true);
	const FString Temp = Path + TEXT(".tmp");
	if (!FFileHelper::SaveStringToFile(Json, *Temp, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		OutError = FString::Printf(TEXT("Could not write %s."), *Temp);
		return false;
	}
	if (!IFileManager::Get().Move(*Path, *Temp, /*bReplace=*/ true))
	{
		OutError = FString::Printf(TEXT("Could not move %s over %s."), *Temp, *Path);
		return false;
	}
	return true;
}

FString FSSLocalDevPersistence::QuarantineRecord(const FString& PlayerId)
{
	const FString Path = PathFor(PlayerId);
	if (Path.IsEmpty() || !IFileManager::Get().FileExists(*Path))
	{
		return FString();
	}
	const FString Aside = FPaths::ChangeExtension(Path, FString::Printf(TEXT("corrupt-%s.json"),
		*FDateTime::UtcNow().ToString(TEXT("%Y%m%d-%H%M%S"))));
	return IFileManager::Get().Move(*Aside, *Path, /*bReplace=*/ false) ? Aside : FString();
}
