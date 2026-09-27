// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSKitSelection.h"
#include "SSClassSelectWidget.generated.h"

class UBorder;
class UTextBlock;
class UWidget;

/**
 * Class selection (on first deployment and after death): Rifleman, Medic,
 * Machine Gunner, Sniper, Grenadier, with the kit each carries (standard or
 * Special Forces, from USSKitSelection). Picking one writes the request to
 * USSKitSelection; the Lyra bridge grants it (respawning at deployment when
 * alive). Built in C++ in the Southern Spear style.
 */
UCLASS()
class SSUI_API USSClassSelectWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Opens the screen (UI input, cursor). bAfterDeath changes the heading. */
	void Open(bool bAfterDeath);
	void Close();

private:
	UFUNCTION() void OnRifleman();
	UFUNCTION() void OnMedic();
	UFUNCTION() void OnMachineGunner();
	UFUNCTION() void OnSniper();
	UFUNCTION() void OnGrenadier();
	void Pick(ESSKitRole Role);
	void Refresh();

	UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Kicker;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> WeaponTexts;
	UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> CardEdges;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Cards;
	float Elapsed = 0.f;
};
