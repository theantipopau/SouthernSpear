// Copyright Southern Spear. All Rights Reserved.

#include "SSMinimapWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/TextBlock.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveHudModel.h"
#include "SSUIStyle.h"
#include "Styling/CoreStyle.h"
#include "SSFonts.h"
#include "SSGlyphTextures.h"

namespace
{
	constexpr int32 MinimapMaxMarkers = 6;
	constexpr float MarkerSize = 22.f;

	UTextBlock* MapText(UWidgetTree* Tree, int32 Size, const FLinearColor& Colour)
	{
		UTextBlock* Text = Tree->ConstructWidget<UTextBlock>();
		Text->SetFont(SSFonts::Display(Size));
		Text->SetColorAndOpacity(Colour);
		Text->SetShadowOffset(FVector2D(1.f, 1.f));
		Text->SetShadowColorAndOpacity(SSUIStyle::Ink950(0.8f));
		return Text;
	}

	UCanvasPanelSlot* Place(UCanvasPanel* Canvas, UWidget* Child, const FVector2D& Size)
	{
		UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Child);
		Slot->SetSize(Size);
		Slot->SetAlignment(FVector2D(0.5f, 0.5f));
		return Slot;
	}
}

bool USSMinimapWidget::Initialize()
{
	return Super::Initialize();
}

void USSMinimapWidget::Setup(ASSObjectiveAssaultDirector* InDirector, bool bInFullMap)
{
	Director = InDirector;
	bFullMap = bInFullMap;
	MapSize = bFullMap ? 760.f : 200.f;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Frame: brass top rule and a field-dark plate, as on the objective panel.
	UBorder* Frame = T->ConstructWidget<UBorder>();
	Frame->SetBrushColor(SSUIStyle::Line(0.95f));
	Frame->SetPadding(FMargin(2.f, 3.f, 2.f, 2.f));
	UCanvasPanelSlot* FrameSlot = Root->AddChildToCanvas(Frame);
	FrameSlot->SetSize(FVector2D(MapSize + 4.f, MapSize + 5.f));
	if (bFullMap)
	{
		FrameSlot->SetAnchors(FAnchors(0.5f, 0.5f));
		FrameSlot->SetAlignment(FVector2D(0.5f, 0.5f));
	}
	else
	{
		FrameSlot->SetAnchors(FAnchors(1.f, 0.f));
		FrameSlot->SetAlignment(FVector2D(1.f, 0.f));
		FrameSlot->SetPosition(FVector2D(-20.f, 4.f));
	}

	UCanvasPanel* Inner = T->ConstructWidget<UCanvasPanel>();
	Frame->SetContent(Inner);
	MapImage = T->ConstructWidget<UImage>();
	MapImage->SetColorAndOpacity(FLinearColor(0.85f, 0.85f, 0.8f, 1.f));
	UCanvasPanelSlot* ImageSlot = Inner->AddChildToCanvas(MapImage);
	ImageSlot->SetSize(FVector2D(MapSize, MapSize));

	Markers = T->ConstructWidget<UCanvasPanel>();
	UCanvasPanelSlot* MarkerSlot = Inner->AddChildToCanvas(Markers);
	MarkerSlot->SetSize(FVector2D(MapSize, MapSize));

	for (int32 Index = 0; Index < MinimapMaxMarkers; ++Index)
	{
		UBorder* Marker = T->ConstructWidget<UBorder>();
		Marker->SetBrushColor(SSUIStyle::Field800(0.9f));
		Marker->SetHorizontalAlignment(HAlign_Center);
		Marker->SetVerticalAlignment(VAlign_Center);
		UTextBlock* Letter = MapText(T, 11, SSUIStyle::Sand100());
		Marker->SetContent(Letter);
		Marker->SetVisibility(ESlateVisibility::Collapsed);
		Place(Markers, Marker, FVector2D(MarkerSize, MarkerSize));
		ObjectiveMarkers.Add(Marker);
		ObjectiveLetters.Add(Letter);
	}

	// A drawn triangle: the UI fonts have no "▲" glyph (the text arrow rendered as nothing).
	const float ArrowSize = bFullMap ? 18.f : 14.f;
	PlayerArrowOutline = T->ConstructWidget<UImage>();
	PlayerArrowOutline->SetBrushFromTexture(SSGlyphTextures::Triangle(), /*bMatchSize=*/ false);
	PlayerArrowOutline->SetColorAndOpacity(SSUIStyle::Ink900());
	PlayerArrowOutline->SetRenderTransformPivot(FVector2D(0.5f, 0.55f));
	Place(Markers, PlayerArrowOutline, FVector2D(ArrowSize + 7.f, ArrowSize + 7.f));
	PlayerArrow = T->ConstructWidget<UImage>();
	PlayerArrow->SetBrushFromTexture(SSGlyphTextures::Triangle(), /*bMatchSize=*/ false);
	PlayerArrow->SetColorAndOpacity(SSUIStyle::Brass300());
	PlayerArrow->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
	Place(Markers, PlayerArrow, FVector2D(ArrowSize, ArrowSize));

	UTextBlock* Label = MapText(T, 10, SSUIStyle::Sage400());
	Label->SetText(bFullMap ? NSLOCTEXT("SSMap", "FullHint", "MAP  ·  M TO CLOSE") : NSLOCTEXT("SSMap", "North", "N"));
	UCanvasPanelSlot* LabelSlot = Markers->AddChildToCanvas(Label);
	LabelSlot->SetAutoSize(true);
	LabelSlot->SetPosition(FVector2D(8.f, 6.f));
}

void USSMinimapWidget::NativeDestruct()
{
	if (Capture)
	{
		Capture->Destroy();
		Capture = nullptr;
	}
	Super::NativeDestruct();
}

void USSMinimapWidget::EnsureCapture()
{
	UWorld* World = GetWorld();
	if (Capture || !World || !MapImage)
	{
		return;
	}
	const int32 Resolution = bFullMap ? 1024 : 384;
	Target = NewObject<UTextureRenderTarget2D>(this);
	Target->InitAutoFormat(Resolution, Resolution);
	Target->ClearColor = SSUIStyle::Ink900();

	FActorSpawnParameters Params;
	Params.ObjectFlags |= RF_Transient;
	Capture = World->SpawnActor<ASceneCapture2D>(FVector::ZeroVector, FRotator(-90.f, 0.f, 0.f), Params);
	if (!Capture)
	{
		return;
	}
	USceneCaptureComponent2D* Comp = Capture->GetCaptureComponent2D();
	Comp->ProjectionType = ECameraProjectionMode::Orthographic;
	Comp->TextureTarget = Target;
	Comp->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	Comp->bCaptureEveryFrame = false;
	Comp->bCaptureOnMovement = false;
	Comp->ShowFlags.SetFog(false);
	Comp->ShowFlags.SetVolumetricFog(false);
	Comp->ShowFlags.SetAtmosphere(false);
	Comp->ShowFlags.SetCloud(false);
	Comp->ShowFlags.SetMotionBlur(false);
	// Cheap top-down pass: no GI, reflections, shadows or post effects.
	Comp->ShowFlags.SetLumenGlobalIllumination(false);
	Comp->ShowFlags.SetLumenReflections(false);
	Comp->ShowFlags.SetGlobalIllumination(false);
	Comp->ShowFlags.SetDynamicShadows(false);
	Comp->ShowFlags.SetAmbientOcclusion(false);
	Comp->ShowFlags.SetScreenSpaceReflections(false);
	Comp->ShowFlags.SetBloom(false);
	Comp->ShowFlags.SetEyeAdaptation(false);
	Comp->ShowFlags.SetParticles(false);
	Comp->ShowFlags.SetSkeletalMeshes(false);
	Comp->ShowFlags.SetTranslucency(false);
	Comp->LODDistanceFactor = 4.f;
	MapImage->SetBrushResourceObject(Target);
	MapImage->SetDesiredSizeOverride(FVector2D(MapSize, MapSize));
}

void USSMinimapWidget::Refresh()
{
	EnsureCapture();
	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (bFullMap && Dir)
	{
		// Frame every objective with a generous margin.
		FBox Bounds(ForceInit);
		for (const ASSObjectiveActor* Objective : Dir->GetObjectives())
		{
			if (Objective)
			{
				Bounds += Objective->GetActorLocation();
			}
		}
		if (const APawn* Pawn = GetOwningPlayerPawn())
		{
			Bounds += Pawn->GetActorLocation();
		}
		if (Bounds.IsValid)
		{
			Centre = Bounds.GetCenter();
			const FVector Extent = Bounds.GetExtent();
			WorldWidth = FMath::Max(30000.f, 2.4f * FMath::Max(Extent.X, Extent.Y));
		}
	}
	if (Capture)
	{
		USceneCaptureComponent2D* Comp = Capture->GetCaptureComponent2D();
		Comp->OrthoWidth = WorldWidth;
		Capture->SetActorLocation(Centre + FVector(0.f, 0.f, 30000.f));
		Comp->CaptureScene();
		ImageCentre = Centre;
	}
}

FVector USSMinimapWidget::PullInsideGround(const FVector& Location) const
{
	const UWorld* World = GetWorld();
	if (!World)
	{
		return Location;
	}
	auto Ground = [World](const FVector& At)
	{
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SSMinimapGround));
		return World->LineTraceTestByChannel(At + FVector(0.f, 0.f, 100000.f), At - FVector(0.f, 0.f, 100000.f), ECC_WorldStatic, Params);
	};
	const float Half = WorldWidth * 0.5f;
	FVector View = Location;
	for (const FVector& Dir : { FVector::ForwardVector, -FVector::ForwardVector, FVector::RightVector, -FVector::RightVector })
	{
		// Up to half a view (in 5 m steps): the player stays on the map even at the ground's edge.
		for (int32 Step = 0; Step < 12 && !Ground(View + Dir * Half); ++Step)
		{
			View -= Dir * FMath::Min(500.f, Half / 12.f + 1.f);
		}
	}
	return View;
}

FVector2D USSMinimapWidget::WorldToMap(const FVector& World) const
{
	// Looking straight down with yaw 0: image up is world +X, image right is +Y.
	const float Scale = MapSize / WorldWidth;
	return FVector2D(MapSize * 0.5f + (World.Y - ImageCentre.Y) * Scale, MapSize * 0.5f - (World.X - ImageCentre.X) * Scale);
}

void USSMinimapWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	const APawn* Pawn = GetOwningPlayerPawn();
	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (!Markers || !Dir)
	{
		return;
	}

	if (!bFullMap)
	{
		// Re-render only after moving 15% of the view; markers move every frame.
		if (Pawn && (!Capture || FVector::Dist2D(Pawn->GetActorLocation(), LastRefreshPawn) > WorldWidth * 0.15f))
		{
			LastRefreshPawn = Pawn->GetActorLocation();
			Centre = PullInsideGround(LastRefreshPawn);
			Refresh();
		}
		else if (!Pawn && !Capture)
		{
			Refresh();
		}
	}

	ESSTeamId ViewerTeam = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(GetOwningPlayer()))
	{
		ViewerTeam = Dir->ToTeamId(Agent->GetGenericTeamId());
	}
	const TArray<TObjectPtr<ASSObjectiveActor>>& Objectives = Dir->GetObjectives();
	TArray<FSSObjectiveState> States;
	for (const ASSObjectiveActor* Objective : Objectives)
	{
		States.Add(Objective ? Objective->GetObjectiveState() : FSSObjectiveState());
	}
	FSSObjectiveHudModel Model;
	Model.BuildChips(States, Dir->GetRoundState().ActiveObjectiveIndex, ViewerTeam);

	const float Edge = MarkerSize * 0.5f + 2.f;
	for (int32 Index = 0; Index < ObjectiveMarkers.Num(); ++Index)
	{
		UBorder* Marker = ObjectiveMarkers[Index];
		const ASSObjectiveActor* Objective = Objectives.IsValidIndex(Index) ? Objectives[Index].Get() : nullptr;
		if (!Objective || !Model.Chips.IsValidIndex(Index))
		{
			Marker->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const FSSObjectiveHudModel::FChip& Chip = Model.Chips[Index];
		// Off-map objectives are pinned to the edge, so the direction still reads.
		FVector2D At = WorldToMap(Objective->GetActorLocation());
		At.X = FMath::Clamp(At.X, Edge, MapSize - Edge);
		At.Y = FMath::Clamp(At.Y, Edge, MapSize - Edge);
		Cast<UCanvasPanelSlot>(Marker->Slot)->SetPosition(At);
		const FLinearColor Tone = SSUIStyle::ToneColour(Chip.OwnerTone);
		Marker->SetBrushColor(Chip.bActive ? Tone : SSUIStyle::Field800(0.9f));
		ObjectiveLetters[Index]->SetText(Chip.Letter);
		ObjectiveLetters[Index]->SetColorAndOpacity(Chip.bActive ? SSUIStyle::Ink950() : Tone);
		Marker->SetVisibility(ESlateVisibility::HitTestInvisible);
	}

	if (PlayerArrow)
	{
		const ESlateVisibility Shown = Pawn ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
		PlayerArrow->SetVisibility(Shown);
		PlayerArrowOutline->SetVisibility(Shown);
		if (Pawn)
		{
			const FVector2D At = WorldToMap(Pawn->GetActorLocation()).ClampAxes(8.f, MapSize - 8.f);
			const float Yaw = GetOwningPlayer() ? GetOwningPlayer()->GetControlRotation().Yaw : Pawn->GetActorRotation().Yaw;
			for (UImage* Image : { PlayerArrowOutline.Get(), PlayerArrow.Get() })
			{
				Cast<UCanvasPanelSlot>(Image->Slot)->SetPosition(At);
				Image->SetRenderTransformAngle(Yaw);
			}
		}
	}
}
