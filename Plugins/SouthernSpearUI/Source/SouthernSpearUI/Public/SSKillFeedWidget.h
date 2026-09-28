// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSKillFeedWidget.generated.h"

class UBorder;
class UTextBlock;

/**
 * Kill feed (top right, under the minimap): "killer  WEAPON  victim", newest on top, viewer-relative colours
 * (friendly sage, opposing clay, the viewer brass). And the viewer's own kill, below the crosshair:
 * "ELIMINATED  <name>". Reads USSKillFeedState (Core), which the Lyra bridge fills. Built in C++.
 */
UCLASS()
class SSUI_API USSKillFeedWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	struct FRowWidgets
	{
		UBorder* Plate = nullptr;
		UTextBlock* Killer = nullptr;
		UTextBlock* Weapon = nullptr;
		UTextBlock* Victim = nullptr;
	};
	TArray<FRowWidgets> Rows;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Keep;
	UPROPERTY(Transient) TObjectPtr<UWidget> Confirm;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ConfirmName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ConfirmWeapon;
	UPROPERTY(Transient) TObjectPtr<UWidget> Death;
	UPROPERTY(Transient) TObjectPtr<UBorder> DeathWash;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DeathBy;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DeathTitle;
};
