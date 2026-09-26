// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/SoftObjectPath.h"
#include "SSFactionPresentationTypes.generated.h"

/**
 * Which cosmetic faction presentation a subject is drawn with.
 *
 * Purely cosmetic and derived per viewer from ESSLocality. It is never an
 * identity: the same player is ACR3 to their own team and MAF to the other.
 * Never replicate it and never branch gameplay on it.
 */
UENUM(BlueprintType)
enum class ESSFactionPresentationId : uint8
{
	/** No presentation. Only ever seen on missing data or a failed resolution. */
	None	UMETA(DisplayName = "None"),

	/** 3rd Battalion, Australian Commonwealth Regiment (fictional). */
	ACR3	UMETA(DisplayName = "3 ACR"),

	/** Murasian Armed Forces (fictional). */
	MAF		UMETA(DisplayName = "MAF"),
};

/**
 * Cosmetic content for one faction presentation.
 *
 * ADR-004: cosmetic fields only. No damage, health, armour, ammunition,
 * movement, collision, hitbox, ability or authority data, and no gameplay type
 * reachable from here. References are soft paths so this data never forces a
 * load and never owns gameplay objects.
 */
USTRUCT(BlueprintType)
struct FSSFactionPresentation
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	ESSFactionPresentationId PresentationId = ESSFactionPresentationId::None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FText DisplayName;

	/** Character mesh. Placeholder only; no final character art exists. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FSoftObjectPath CharacterMesh;

	/** Uniform material. Placeholder only; CMECU / red-earth work not started. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FSoftObjectPath UniformMaterial;

	/** UI icon. Placeholder only. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FSoftObjectPath Icon;

	/** True when every field needed to draw this presentation is present. */
	bool IsComplete() const
	{
		return PresentationId != ESSFactionPresentationId::None
			&& !DisplayName.IsEmpty()
			&& CharacterMesh.IsValid()
			&& UniformMaterial.IsValid()
			&& Icon.IsValid();
	}
};

/** The presentations a resolution selects from, keyed by viewer locality. */
USTRUCT(BlueprintType)
struct FSSFactionPresentationTable
{
	GENERATED_BODY()

	/** How the viewer's own team is drawn (3 ACR). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FSSFactionPresentation Friendly;

	/** How the other team is drawn (MAF). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation")
	FSSFactionPresentation Opposing;
};
