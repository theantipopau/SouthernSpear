// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSMinimapWidget.generated.h"

class ASceneCapture2D;
class ASSObjectiveAssaultDirector;
class UBorder;
class UCanvasPanel;
class UImage;
class UTextBlock;
class UTextureRenderTarget2D;

/**
 * Top-down map for the local player, built in C++ (no Blueprint asset).
 * Minimap: north-up, centred on the player, refreshed a few times a second.
 * Full map (toggled by the HUD subsystem): the whole objective area, captured
 * once when opened. Both draw the objectives as lettered markers in viewer-
 * relative tones (FSSObjectiveHudModel) and the player as an arrow. The scene
 * capture is a client-local actor; nothing replicates.
 */
UCLASS()
class SSOBJUI_API USSMinimapWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Call before AddToViewport. */
	void Setup(ASSObjectiveAssaultDirector* InDirector, bool bInFullMap);

	/** Full map: re-capture now (on open). */
	void Refresh();

private:
	void EnsureCapture();
	FVector2D WorldToMap(const FVector& World) const;

	TWeakObjectPtr<ASSObjectiveAssaultDirector> Director;
	bool bFullMap = false;
	float MapSize = 220.f;
	float WorldWidth = 12000.f; // cm across the map image
	FVector Centre = FVector::ZeroVector;
	FVector ImageCentre = FVector::ZeroVector;
	/** Pawn location at the last re-render (the view centre itself may be pulled in from it). */
	FVector LastRefreshPawn = FVector::ZeroVector;
	/** Moves the view centre inward until every view edge has ground under it, so the corner map
	 * never shows the void past the level's ground (downward traces, only when re-rendering). */
	FVector PullInsideGround(const FVector& Location) const;

	UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> Target;
	UPROPERTY(Transient) TObjectPtr<ASceneCapture2D> Capture;
	UPROPERTY(Transient) TObjectPtr<UCanvasPanel> Markers;
	UPROPERTY(Transient) TObjectPtr<UImage> MapImage;
	UPROPERTY(Transient) TObjectPtr<UImage> PlayerArrow;
	/** Dark outline under the arrow: pale brass alone disappears on the sand-coloured map. */
	UPROPERTY(Transient) TObjectPtr<UImage> PlayerArrowOutline;
	UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> ObjectiveMarkers;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> ObjectiveLetters;
};
