// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SSObjectivesEditorLibrary.generated.h"

class UGameFeatureData;

/** One component a Game Feature adds to an actor class. Python-friendly mirror of FGameFeatureComponentEntry. */
USTRUCT(BlueprintType)
struct FSSComponentGrant
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Components")
	FSoftClassPath ActorClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Components")
	FSoftClassPath ComponentClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Components")
	bool bClientComponent = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Components")
	bool bServerComponent = true;
};

/**
 * Editor authoring helpers. The engine does not expose FGameFeatureComponentEntry
 * to Python, so the Objective Assault setup script builds its AddComponents
 * action through here.
 */
UCLASS()
class USSObjectivesEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Replace every AddComponents action on Data with a single one granting
	 * exactly Grants. Returns the number of entries written, or -1 on failure.
	 * The caller saves the asset.
	 */
	UFUNCTION(BlueprintCallable, Category = "Southern Spear|Editor")
	static int32 SetGameFeatureComponentGrants(UGameFeatureData* Data, const TArray<FSSComponentGrant>& Grants);

	/**
	 * Set a property on an instance from its text form, bypassing the
	 * EditDefaultsOnly check that blocks Python. Editor authoring only (used
	 * for LyraWorldSettings.DefaultGameplayExperience). Returns false, and logs,
	 * if the property does not exist or the text does not parse.
	 */
	UFUNCTION(BlueprintCallable, Category = "Southern Spear|Editor")
	static bool SetPropertyFromText(UObject* Target, FName PropertyName, const FString& Value);

	/** Export a property as text (the inverse of SetPropertyFromText); empty if missing. */
	UFUNCTION(BlueprintCallable, Category = "Southern Spear|Editor")
	static FString GetPropertyAsText(UObject* Target, FName PropertyName);
};
