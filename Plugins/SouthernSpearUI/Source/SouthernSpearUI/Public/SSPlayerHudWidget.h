// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSPlayerHudWidget.generated.h"

class UBorder;
class UHorizontalBoxSlot;
class UTextBlock;
class UWidget;

/**
 * Southern Spear player HUD, built in C++: health (bottom left), ammunition and
 * weapon (bottom right), a crosshair that opens with movement and hides when
 * aiming, and a clay edge flash when hit. Reads USSLocalHudState only.
 */
UCLASS()
class SSUI_API USSPlayerHudWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	UPROPERTY(Transient) TObjectPtr<UWidget> HealthPanel;
	UPROPERTY(Transient) TObjectPtr<UWidget> AmmoPanel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HealthText;
	UPROPERTY(Transient) TObjectPtr<UBorder> HealthFill;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MagazineText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ReserveText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> WeaponText;
	UPROPERTY(Transient) TObjectPtr<UWidget> Crosshair;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> CrosshairTicks;
	UPROPERTY(Transient) TObjectPtr<UBorder> DamageFlash;
	UPROPERTY(Transient) TObjectPtr<class UImage> HitArrow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ReloadHint;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> FpsText;
	/** Scope view (aiming a magnified optic): eyepiece mask, black sides, reticle. */
	UPROPERTY(Transient) TObjectPtr<UWidget> ScopeOverlay;
	UPROPERTY(Transient) TObjectPtr<class USizeBox> ScopeEyepiece;
	float FpsAverage = 1.f / 60.f;
	float FpsRefresh = 0.f;
	float Elapsed = 0.f;

	UHorizontalBoxSlot* HealthFillSlot = nullptr;
	UHorizontalBoxSlot* HealthEmptySlot = nullptr;
	float LastHealth = -1.f;
	float FlashAlpha = 0.f;
	float Spread = 10.f;
};
