// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSLoadingScreenWidget.generated.h"

class UImage;
class UTextBlock;
class UWidget;

/**
 * Southern Spear loading screen. When the destination is an operation (SSOperations) it names it:
 * "LOADING · RED GUM STATION", the map's line and description, the rule set and what it asks of you, and
 * the map's own art when there is some (T_SS_Load_<Key>), else the key art. Any other load (the front
 * end, a map not in the list) gets the key art and the wordmark. A play tip either way. Used by
 * CommonLoadingScreen (Config/DefaultGame.ini LoadingScreenWidget).
 */
UCLASS()
class SSUI_API USSLoadingScreenWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	/** Where this load is going and under which rules: the front end's request, else the engine's travel URL. */
	void ResolveDestination(FString& OutMap, bool& bOutSection) const;

	UPROPERTY(Transient) TObjectPtr<UImage> Art;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Kicker;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Title;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Meta;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Description;
	UPROPERTY(Transient) TObjectPtr<UWidget> ModeBlock;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ModeName;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ModeSummary;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LoadingText;
	float Elapsed = 0.f;
};
