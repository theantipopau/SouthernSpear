// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSCompassWidget.generated.h"

class ASSObjectiveAssaultDirector;
class UBorder;
class UCanvasPanel;
class UTextBlock;

/**
 * Heading strip under the objective panel: cardinal letters and degree ticks
 * scrolling with the view, plus a lettered marker and distance for each
 * objective in its viewer-relative tone. Built in C++; reads replicated state.
 */
UCLASS()
class SSOBJUI_API USSCompassWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(ASSObjectiveAssaultDirector* InDirector);
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	TWeakObjectPtr<ASSObjectiveAssaultDirector> Director;

	UPROPERTY(Transient) TObjectPtr<UCanvasPanel> Strip;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> Labels;     // one per 15 degrees
	UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Markers;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> MarkerLetters;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> MarkerDistances;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HeadingText;
};
