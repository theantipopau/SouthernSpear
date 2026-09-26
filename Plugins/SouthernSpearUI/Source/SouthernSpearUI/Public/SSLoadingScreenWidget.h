// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSLoadingScreenWidget.generated.h"

class UTextBlock;

/**
 * Southern Spear loading screen: full-bleed key art with a field-dark band,
 * an animated LOADING label and a play tip. Used by CommonLoadingScreen
 * (Config/DefaultGame.ini LoadingScreenWidget).
 */
UCLASS()
class SSUI_API USSLoadingScreenWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	UPROPERTY(Transient) TObjectPtr<UTextBlock> LoadingText;
	float Elapsed = 0.f;
};
